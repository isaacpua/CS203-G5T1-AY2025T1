import json
from langchain.schema import HumanMessage
from data_analysis.utils.llm import llm

def summarize_with_llm(result: dict, user_prompt: str, max_chars: int = 5000) -> dict:
    """
    Generates a plain-language summary of the result using LLM. 
    Truncates large fields and uses intent-specific instructions.
    """
    intent = result.get("intent", "").lower()
    print(f"Summarizing result for intent: {intent}")

    OMIT_KEYS = [
        "plotly_data", "plotly_layout", 
        "boxplot_data", "histogram_data", "contingency_table"
    ]

    INSTRUCTION_MAP = {
        "regression": (
            "You are a helpful data analysis assistant. Write a structured, well-organized interpretation "
            "of the regression results in plain English. Do not use Markdown or LaTeX.\n\n"
            "Your response must be formatted using numbered sections with clear headers in title case, like this:\n"
            "1. Regression Equation: ...\n"
            "2. R-Squared Value: ...\n"
            "3. Significant Coefficients: ...\n"
            "4. Heteroskedasticity: ...\n"
            "5. Model Specification: ...\n\n"
            "Include:\n"
            "- The regression equation and what it means\n"
            "- What the R-squared value indicates\n"
            "- Significance and meaning of the coefficients\n"
            "- If heteroskedasticity was detected\n"
            "- Whether the model passed the Ramsey RESET test or had specification issues"
        ),
        "describe": (
            "You are a helpful assistant. Summarize the descriptive statistics clearly.\n"
            "- Mention range, mean, variability\n"
            "- Note any outliers\n"
            "- Highlight patterns from histogram or boxplot\n"
            "Avoid Markdown or LaTeX."
        ),
        "region analysis": (
            "Interpret a Getis-Ord Gi* hot spot analysis in plain English. "
            "Structure your response with numbered sections and title case headers, like:\n"
            "1. Z-Scores and P-Values: ...\n"
            "2. Hot and Cold Spots: ...\n"
            "3. Spatial Clustering Implications: ...\n\n"
            "Avoid using Markdown or LaTeX formatting. Keep the language clear and consistent."
        ),
        "regionforecast": (
            "You are a helpful data analysis assistant. Interpret the results of a region-based forecast using a STARMA or STARIMA model.\n\n"
            "Include:\n"
            "- An explanation of the STARIMA/STARMA model and how it works (temporal and spatial lags)\n"
            "- The meaning and values of the selected model parameters (p, d, q)\n"
            "- Explanation of what the forecast horizon represents\n"
            "- Discussion of key performance metrics (include actual values):\n"
            "  - BIC (Bayesian Information Criterion)\n"
            "  - RMSE (Root Mean Squared Error)\n"
            "  - MAE (Mean Absolute Error)\n"
            "  - Log-likelihood\n"
            "- Identify the top 3 regions with the highest forecasted values and describe their trends\n"
            "- Ensure the explanation is specific to the provided data (mention actual values where relevant)\n\n"
            "Avoid technical jargon unless necessary, and do not use Markdown or LaTeX."
        ),
        "forecast": (
            "You are a helpful data analysis assistant. Interpret the results of a time series forecast "
            "generated using a statistical or machine learning model.\n\n"
            "Your response must be structured using numbered sections with clear headers in title case, such as:\n"
            "1 - Forecasted Values\n"
            "2 - Trend and Direction\n"
            "3 - Confidence Intervals\n"
            "4 - Volatility and Uncertainty\n\n"
            "Include:\n"
            "- A summary of the forecasted values and the time horizon\n"
            "- Whether the forecast shows an upward, downward, or flat trend\n"
            "- The width of the confidence intervals and what that implies about certainty\n"
            "- Any notable outliers, spikes, or turning points in the predictions\n"
            "- Whether the variability suggests the need for caution in interpretation\n\n"
            "Avoid using Markdown or LaTeX. Keep the explanation specific, clear, and aligned with the actual forecast values."
        ),
    }

    # Step 1: Reduce large fields
    reduced = result.copy()
    for key in OMIT_KEYS:
        if key in reduced:
            reduced[key] = f"<{key} omitted for brevity>"

    try:
        json_str = json.dumps(reduced, indent=2)
        truncated = json_str if len(json_str) <= max_chars else json_str[:max_chars] + "\n... (truncated)"
    except Exception as e:
        result["llm_summary"] = f"Could not serialize result: {e}"
        return result

    # Step 2: Generate extra notes based on intent
    extra_note = ""
    if intent == "regression" and "equation" in result:
        extra_note = f"Regression equation:\n{result['equation']}\n\n"

    elif intent == "regionforecast":
        metrics = result.get("metrics", {})
        bic = metrics.get("bic", "N/A")
        rmse = metrics.get("rmse", "N/A")
        mae = metrics.get("mae", "N/A")
        loglik = metrics.get("loglikelihood", "N/A")
        extra_note += (
            "Performance Metrics:\n"
            f"- BIC: {bic:.2f}\n"
            f"- RMSE: {rmse:.2f}\n"
            f"- MAE: {mae:.2f}\n"
            f"- Log-Likelihood: {loglik:.2f}\n\n"
        )

        # Add Top 3 regions by forecasted total
        try:
            from collections import defaultdict
            region_totals = defaultdict(float)
            for row in result.get("forecast_summary", []):
                if row.get("type") == "Forecast":
                    region = row.get("region")
                    forecast_val = float(row.get("forecast", 0))
                    region_totals[region] += forecast_val
            top_3 = sorted(region_totals.items(), key=lambda x: x[1], reverse=True)[:3]
            extra_note += "Top 3 regions with highest total forecasted values:\n"
            for i, (region, total) in enumerate(top_3, 1):
                extra_note += f"{i}. {region} - Total Forecast: {total:.2f}\n"
            extra_note += "\n"
        except Exception as e:
            extra_note += f"[Top regions could not be identified: {e}]\n\n"

    # Step 3: Final Prompt
    instructions = INSTRUCTION_MAP.get(intent,
        "Write a clear and concise interpretation of the results in plain English for a data analyst."
    )

    summary_prompt = (
        f"A user asked: \"{user_prompt}\"\n\n"
        f"{extra_note}"
        f"Here are the computed results:\n\n"
        f"{truncated}\n\n"
        f"{instructions}"
    )

    # Step 4: LLM call
    try:
        response = llm().invoke([HumanMessage(content=summary_prompt)])
        result["llm_summary"] = response.content.strip()
    except Exception as e:
        result["llm_summary"] = f"Failed to generate summary: {e}"

    return result