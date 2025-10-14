import re
import difflib
import logging
import pandas as pd
from typing import List, Dict
from data_analysis.utils.llm import llm
from langchain.schema import HumanMessage
import json

def extract_columns_from_prompt(prompt: str, valid_columns: List[str], intent: str = None, chart_type: str = None) -> Dict[str, List[str]]:
    print(f"[DEBUG] Intent passed to extract_columns_from_prompt: {intent}")
    column_str = ", ".join(valid_columns)

    def fuzzy_match(word: str, choices: List[str]) -> str | None:
        matches = difflib.get_close_matches(word.lower(), [c.lower() for c in choices], n=1, cutoff=0.6)
        if matches:
            index = [c.lower() for c in choices].index(matches[0])
            return choices[index]
        return None

    if chart_type == "choropleth":
        full_prompt = (
            f"The dataset has these columns: {column_str}.\n"
            f"From this user question:\n\"{prompt}\"\n"
            f"Which column represents the region (e.g., town, district) and which one is the value to be mapped?\n"
            "Return only a valid JSON object like: {\"region\": [\"District\"], \"value\": [\"Resale_Price\"]}\n"
            "Do not include any explanation or markdown."
        )
        try:
            response = llm().invoke([HumanMessage(content=full_prompt)])
            raw_text = response.content.strip()
            match = re.search(r"{.*?}", raw_text, re.DOTALL)
            parsed = json.loads(match.group(0)) if match else {}
            return {
                "region": parsed.get("region", []),
                "value": parsed.get("value", []),
                "columns": parsed.get("region", []) + parsed.get("value", [])
            }
        except Exception as e:
            print(f"[extract_columns_from_prompt] Error: {e}")
            return {"region": [], "value": [], "columns": []}

    if intent == "regression":
        match = re.search(r"regress\s+(.+?)\s+on\s+(.+)", prompt, re.IGNORECASE)
        if not match:
            print("Pattern 'regress ... on ...' not found in prompt.")
            return {"target": [], "features": []}

        raw_target = match.group(1).strip()
        raw_features = match.group(2).strip()
        feature_candidates = re.split(r",|\band\b", raw_features)

        matched_target = fuzzy_match(raw_target, valid_columns)
        matched_features = [fuzzy_match(f.strip(), valid_columns) for f in feature_candidates]
        matched_features = [f for f in matched_features if f and f != matched_target]

        return {
            "target": [matched_target] if matched_target else [],
            "features": matched_features
        }

    if intent == "forecast":
        full_prompt = (
            f"The dataset has columns: {column_str}.\n"
            f"User prompt: \"{prompt}\"\n\n"
            "You are configuring Prophet for a time series forecast.\n"
            "- Choose a date/time column (for 'ds')\n"
            "- Choose a numeric column to predict (for 'y')\n"
            "- Extract the number of future periods to forecast\n\n"
            "Return ONLY in this format:\n"
            "ds: <date_column_name>\n"
            "y: <value_column_name>\n"
            "periods: <number_of_periods>"
        )
        try:
            reply = llm()([HumanMessage(content=full_prompt)]).content.strip().lower()
            date_match = re.search(r"^ds\s*:\s*(.+)$", reply, re.MULTILINE)
            value_match = re.search(r"^y\s*:\s*(.+)$", reply, re.MULTILINE)
            periods_match = re.search(r"^periods\s*:\s*(\d+)", reply, re.MULTILINE)

            raw_date = date_match.group(1).strip() if date_match else ""
            raw_value = value_match.group(1).strip() if value_match else ""
            raw_periods = int(periods_match.group(1)) if periods_match else 30

            matched_date = fuzzy_match(raw_date, valid_columns)
            matched_value = fuzzy_match(raw_value, valid_columns)

            return {
                "date": [matched_date] if matched_date else [],
                "value": [matched_value] if matched_value else [],
                "periods": [raw_periods]
            }
        except Exception:
            return {"date": [], "value": [], "periods": [30]}

    if intent == "compare":
        full_prompt = (
            "You are helping to extract **only** the columns explicitly mentioned by the user for a comparison test "
            "(e.g., t-test, ANOVA).\n\n"
            f"The dataset columns are:\n{column_str}\n\n"
            f"User's prompt:\n\"{prompt}\"\n\n"
            "Your task:\n"
            "- Identify which columns the user mentioned for comparison.\n"
            "- Categorize each into either:\n"
            "  - 'group': categorical column(s)\n"
            "  - 'value': numeric column(s)\n\n"
            "Return strictly in JSON format like:\n"
            "{\"group\": [\"GroupColumn\"], \"value\": [\"ValueColumn1\", \"ValueColumn2\"]}\n"
            "Do not guess or add extra columns. Do not include explanation or text."
        )

        try:
            response = llm().invoke([HumanMessage(content=full_prompt)])
            raw_text = response.content.strip()
            print("[LLM RAW RESPONSE]", raw_text)

            match = re.search(r"{[\s\S]*?}", raw_text)
            if not match:
                raise ValueError("No valid JSON object found.")

            parsed = json.loads(match.group(0))

            group_cols = [fuzzy_match(col, valid_columns) for col in parsed.get("group", []) if isinstance(col, str)]
            value_cols = [fuzzy_match(col, valid_columns) for col in parsed.get("value", []) if isinstance(col, str)]

            # Keep only valid matches
            group_cols = [g for g in group_cols if g in valid_columns]
            value_cols = [v for v in value_cols if v in valid_columns]

            print(f"[DEBUG] Extracted group: {group_cols}, value: {value_cols}")

            return {"columns": group_cols + value_cols}

        except Exception as e:
            print(f"[compare parser failed] {e}")
            return {"columns": []}

    if intent == "region":
        full_prompt = (
            "You are helping to extract the relevant column names from a dataset for regional analysis.\n"
            f"The dataset has columns: {column_str}\n"
            f"The user's question is: {prompt}\n\n"
            "Return a valid JSON object using only the **column names** from the dataset.\n"
            "Do NOT return actual values like Town A or date ranges.\n"
            "Format your response exactly like this:\n"
            "{\"region\": [\"<column_name>\"], \"value\": [\"<column_name>\"], \"date\": [\"<column_name>\"], \"periods\": 12}"
        )
        try:
            response = llm().invoke([HumanMessage(content=full_prompt)])
            raw_text = response.content.strip()
            print(f"[DEBUG] LLM raw response:\n{raw_text}")

            # Try parsing raw JSON directly first
            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError:
                # Fallback: extract first JSON-like block from response
                match = re.search(r"{[\s\S]*?}", raw_text)
                if not match:
                    raise ValueError("No valid JSON object found in response.")
                parsed = json.loads(match.group(0))

            print(f"[DEBUG] Parsed JSON: {parsed}")

            # Fuzzy match only if the value is a string
            region = [fuzzy_match(col, valid_columns) for col in parsed.get("region", []) if isinstance(col, str)]
            value = [fuzzy_match(col, valid_columns) for col in parsed.get("value", []) if isinstance(col, str)]
            date = [fuzzy_match(col, valid_columns) for col in parsed.get("date", []) if isinstance(col, str)]

            # Extract periods if possible
            periods = []
            if "periods" in parsed:
                try:
                    periods = [int(parsed["periods"])]
                except (ValueError, TypeError):
                    print("[WARN] Could not parse 'periods' as integer.")

            # Clean up any None or empty values
            region = [c for c in region if c]
            value = [c for c in value if c]
            date = [c for c in date if c]

            if not region:
                print(f"[WARN] No region column matched from: {parsed.get('region')}")
            if not value:
                print(f"[WARN] No value column matched from: {parsed.get('value')}")
            if not date:
                print(f"[INFO] No date column matched from: {parsed.get('date')}")

            return {
                "region": region,
                "value": value,
                "date": date,
                "periods": periods,
                "columns": region + value + date
            }

        except Exception as e:
            print(f"[extract_columns_from_prompt] Failed region parsing: {e}")
            return {"region": [], "value": [], "date": [], "periods": [], "columns": []}
    
    
    if intent == "explore":
        full_prompt = (
            f"The dataset columns are: {column_str}\n"
            f"User instruction: \"{prompt}\"\n\n"
            "Identify the single most relevant column to explore (e.g., to summarize or visualize).\n"
            "Return only the column name in plain text, no explanation."
        )
        try:
            response = llm().invoke([HumanMessage(content=full_prompt)])
            col_candidate = response.content.strip().lower()
            best_match = fuzzy_match(col_candidate, valid_columns)
            if best_match:
                return {"columns": [best_match]}
        except Exception as e:
            print(f"[extract_columns_from_prompt] Failed explore parsing: {e}")

        return {"columns": []}

    if chart_type == "candlestick":
        required = ["Date", "Open", "High", "Low", "Close"]
        return {"columns": [col for col in required if col in valid_columns]}

    if chart_type == "scatter_map":
        full_prompt = (
            f"The dataset has: {column_str}\n"
            f"Prompt: \"{prompt}\"\n"
            "Return ONLY a valid JSON object like: "
            "{\"lat\": \"<column>\", \"lon\": \"<column>\", \"label\": \"<column>\", \"value\": \"<column>\"}\n"
            "Do not include any explanation or text outside the JSON."
        )

        try:
            response = llm().invoke([HumanMessage(content=full_prompt)])
            raw = response.content.strip()
            print(f"[DEBUG] LLM raw response:\n{raw}")  # Add this for diagnostics

            # Greedy match to extract full JSON object and ignore extra text
            match = re.search(r"{[\s\S]+?}", raw)
            if not match:
                raise ValueError("No valid JSON object found in LLM response.")

            parsed = json.loads(match.group(0))

            return {
                "lat": parsed.get("lat"),
                "lon": parsed.get("lon"),
                "label": parsed.get("label"),
                "value": parsed.get("value"),
                "columns": [parsed.get(k) for k in ["lat", "lon", "label", "value"] if parsed.get(k)]
            }

        except Exception as e:
            print(f"[extract_columns_from_prompt] scatter_map error: {e}")
            return {"lat": None, "lon": None, "label": None, "value": None, "columns": []}

    # General fallback case
    full_prompt = (
        f"The dataset columns: {column_str}\nUser prompt: \"{prompt}\"\n"
        "Return only the relevant columns in a comma-separated list, no explanation."
    )
    try:
        response = llm()([HumanMessage(content=full_prompt)])
        reply = response.content.strip()
        raw_keywords = [word.strip() for word in re.split(r",|\band\b", reply)]
        matched = [fuzzy_match(k, valid_columns) for k in raw_keywords if fuzzy_match(k, valid_columns)]
        return {"columns": [m for m in matched if m]}
    except Exception as e:
        print(f"[extract_columns_from_prompt] fallback error: {e}")
        return {"columns": []}