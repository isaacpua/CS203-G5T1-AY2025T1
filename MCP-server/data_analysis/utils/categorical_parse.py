import re
import json
from typing import List, Dict
import pandas as pd
from data_analysis.utils.llm import llm
from langchain.schema import HumanMessage

def extract_categorical_test_info(prompt: str, valid_columns: List[str], df: pd.DataFrame) -> Dict:
    # Prepare dataset summary
    summary_info = []
    for col in valid_columns:
        dtype = str(df[col].dtype)
        nunique = df[col].nunique()
        summary_info.append(f"{col} (type={dtype}, unique={nunique})")
    summary_str = "\n".join(summary_info)

    # Compose LLM prompt
    llm_prompt = (
        "You are a statistical assistant for analyzing **categorical data**.\n\n"
        "Based on the user's question and the dataset columns, identify the **most appropriate statistical test**.\n\n"
        "The possible test types are:\n"
        "- `mcnemar`: Use **only** when comparing two **binary variables** from the **same subjects**, such as pre/post or before/after data (paired observations).\n"
        "- `association`: Use when assessing **relationship between two categorical variables** in a contingency table (e.g., gender vs choice).\n"
        "- `goodness`: Use when checking if **observed frequencies** of a single categorical variable **match expected frequencies**.\n"
        "- `proportion`: Use when comparing the **proportion of a binary outcome across multiple groups**, where the outcome is **not paired**, e.g., recovery rate by hospital.\n\n"
        "Dataset columns:\n"
        f"{summary_str}\n\n"
        f"User prompt:\n\"{prompt}\"\n\n"
        "Return a JSON object in this format:\n"
        "{ \"columns\": [ ... ], \"test_type\": \"...\" }"
    )

    try:
        response = llm().invoke([HumanMessage(content=llm_prompt)])
        raw = response.content.strip()
        raw = re.sub(r"^```(?:json)?\s*|```$", "", raw)

        parsed = json.loads(raw)
        return {
            "columns": parsed.get("columns", []),
            "test_type": parsed.get("test_type", "unknown").lower()
        }

    except Exception as e:
        print(f"LLM parsing error: {e}")
        return {"columns": [], "test_type": "unknown"}