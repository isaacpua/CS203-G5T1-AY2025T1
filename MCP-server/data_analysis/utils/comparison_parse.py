import re
import json
import pandas as pd
from typing import List, Dict
from langchain.schema import HumanMessage
from data_analysis.utils.llm import llm

def normalize_test_type(raw_type: str) -> str:
    raw_type = raw_type.lower()
    if "paired" in raw_type:
        return "paired"
    elif "independent" in raw_type:
        return "independent"
    elif "anova" in raw_type:
        return "anova"
    else:
        return "unknown"

def correct_test_type_if_needed(df: pd.DataFrame, columns: List[str], test_type: str) -> str:
    print(f"[DEBUG] Evaluating test_type correction for columns: {columns}")
    print(f"[DEBUG] Number of columns: {len(columns)}")
    print(f"[DEBUG] Column data types:\n{df[columns].dtypes}")

    numeric_cols = []
    categorical_cols = []

    for col in columns:
        try:
            series = pd.to_numeric(df[col], errors="coerce")
            if pd.api.types.is_numeric_dtype(series):
                numeric_cols.append(col)
            else:
                categorical_cols.append(col)
        except Exception as e:
            print(f"[DEBUG] Error coercing column '{col}': {e}")
            categorical_cols.append(col)

    print(f"[DEBUG] Numeric columns: {numeric_cols}")
    print(f"[DEBUG] Categorical columns: {categorical_cols}")
    print(f"[DEBUG] Initial test_type from LLM: '{test_type}'")

    if len(numeric_cols) >= 3 and len(categorical_cols) == 0:
        print(f"[DEBUG] Forcing test_type='anova' due to 3+ numeric columns: {numeric_cols}")
        return "anova"

    if len(columns) == 2 and len(numeric_cols) == 1 and len(categorical_cols) == 1:
        cat_col = categorical_cols[0]
        num_groups = df[cat_col].dropna().nunique()
        print(f"[DEBUG] Detected 1 numeric + 1 categorical: {numeric_cols[0]} + {cat_col} (groups={num_groups})")
        if test_type == "independent" and num_groups > 2:
            print(f"[DEBUG] Correcting test_type to 'anova' due to >2 groups")
            return "anova"
        elif test_type == "anova" and num_groups <= 2:
            print(f"[DEBUG] Correcting test_type to 'independent' due to ≤2 groups")
            return "independent"

    print(f"[DEBUG] Keeping original test_type='{test_type}'")
    return test_type

def extract_comparison_test_info(prompt: str, valid_columns: List[str], df: pd.DataFrame) -> Dict:
    # Summarize column metadata for LLM
    summary_info = [
        f"{col} (type={df[col].dtype}, unique={df[col].nunique()})"
        for col in valid_columns
    ]
    summary_str = "\n".join(summary_info)

    llm_prompt = (
        "You are a statistical test selector.\n"
        "Choose the correct test based on the user prompt and the column characteristics.\n\n"
        "Rules:\n"
        "- Use `paired` t-test only when the prompt explicitly refers to measuring the same individuals under two different conditions,\n"
        "  such as 'before and after', 'pre and post', or similar wording indicating repeated measurements on the same subjects.\n"
        "- Use `independent` t-test when comparing one numeric column across two independent groups (e.g., gender, class A vs B).\n"
        "- Use `anova` when comparing one numeric column across three or more independent groups.\n\n"
        "Do not infer a paired test unless the prompt clearly uses paired-comparison language like 'before/after', 'pre/post', etc.\n\n"
        f"The dataset has the following columns:\n{summary_str}\n\n"
        f"User prompt: \"{prompt}\"\n\n"
        "Return only a JSON object in this format:\n"
        "{ \"columns\": [\"col1\", \"col2\"], \"test_type\": \"independent\" }\n"
        "Only output the JSON object. Do not include explanations or any extra text."
    )

    try:
        response = llm().invoke([HumanMessage(content=llm_prompt)])
        raw = response.content.strip()

        # Strip markdown if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*|```$", "", raw)

        parsed = json.loads(raw)
        selected_columns = [c.strip() for c in parsed.get("columns", [])]
        test_type = parsed.get("test_type", "unknown").lower()

        # Apply correction logic
        corrected_test_type = correct_test_type_if_needed(df, selected_columns, test_type)
        print(f"[DEBUG] Test type from LLM: '{test_type}', corrected to: '{corrected_test_type}'")

        return {
            "columns": selected_columns,
            "test_type": corrected_test_type
        }

    except Exception as e:
        print(f"LLM or JSON parse error: {e}")
        return {
            "columns": [],
            "test_type": "unknown"
        }