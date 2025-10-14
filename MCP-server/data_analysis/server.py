# server.py
from fastmcp import FastMCP
from typing import List, Dict, Optional
import pandas as pd
from .tools.eda import EDA
from .tools.forecast import Forecast
from .tools.region import RegionAnalysis
from .tools.regression import LinearRegression
from .tools.compare import Comparison
from .tools.categorical import Categorical 
from .tools.plot import Plot
from .utils.prompt_parser import extract_columns_from_prompt
from .utils.plot_parse import infer_chart_type
from .utils.intent import classify_intent
from .utils.interpreter import summarize_with_llm
import geopandas as gpd
import logging
logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="Dex Data Analysis",
    instructions="""
    This MCP server provides advanced data analysis tools that operate on a user-uploaded dataset. It supports the following capabilities:
    - regression: Fit and interpret linear regression models. Supports multiple predictors, automatic handling of binary categorical variables, outlier removal, heteroskedasticity checks (Breusch-Pagan test), and model specification checks (Ramsey RESET). Use for prompts like "Regress test scores on study hours and sleep time".
    - describe: Generate descriptive summaries for numerical or categorical columns. Includes mean, median, standard deviation, histogram, boxplot, outlier detection, frequency counts, skewness classification, and Gini index. Use for prompts like "Describe sales distribution" or "Show outliers in income".
    - compare: Run statistical comparisons between groups. Supports paired and independent t-tests, ANOVA with post-hoc tests, normality checks (Shapiro-Wilk), and non-parametric fallback (Mann-Whitney). Use for prompts like "Compare exam scores between schools" or "Is there a difference in revenue by product type?"
    - categorical: Analyze relationships between categorical variables. Supports chi-squared association tests, goodness-of-fit tests, McNemar test (for paired binary), and proportion tests. Includes visualizations (heatmaps, bar charts, dot plots). Use for prompts like "Check association between gender and response" or "Are vote proportions equal?"
    - plot: Generate visualizations based on selected columns. Supports histogram, bar chart, scatterplot, line plot, pie chart, and boxplot. Automatically infers best chart type from prompt and column types. Use for prompts like "Plot income distribution" or "Bar chart of product sales".
    - forecast: Perform time series forecasting using Prophet. Automatically identifies date and value columns. Includes forecast chart and numeric forecast table. Use for prompts like "Forecast next 6 months of sales" or "Predict electricity usage".
    - region analysis: Analyze and forecast spatio-temporal trends across regions (e.g. towns or planning areas). Uses STARIMA models if data is stationary, otherwise STARMA. Identifies regional hotspots and generates animated choropleth maps over time. Use for prompts like "Forecast dengue cases by region" or "Identify regional housing price trends".

    To use this server, provide a natural language prompt such as:
    - "Regress performance index on hours studied and previous scores"
    - "Describe the distribution of sleep hours"
    - "Compare test scores between male and female students"
    - "Plot histogram of income"
    - "Forecast future electricity demand for the next x periods"
    - "Perform a region analysis of price for each town"
    - "Perform a region forecast of price for each town for the next x periods"

    The system will classify the prompt and automatically route it to the appropriate analysis tool.
    The user-uploaded dataset (CSV, Excel, or table extracted from PDF) is automatically loaded and passed to the selected tool as a Pandas DataFrame named `df`. All tools operate directly on this DataFrame based on the user's prompt.
    """
)

# === run_analysis **used for data analysis**===
@mcp.tool(
    name="run_analysis",
    description=(
        "Analyzes a dataset based on the user's natural language prompt. "
        "Supports regression, descriptive statistics, plotting, group comparisons (e.g., t-test, ANOVA), "
        "time series forecasting, categorical analysis (e.g., chi-squared, McNemar), and region-based analysis "
        "(e.g., spatio-temporal forecasting using STARIMA). The uploaded file is passed as a list of records (dicts)."
    )
)
async def run_analysis(data: List[Dict], user_prompt: str, geojson: Optional[Dict] = None):
    df = pd.DataFrame(data)
    intent = classify_intent(user_prompt)
    print(f"[DEBUG] Detected intent: {intent}")

    if intent == "describe":
        result = explore(prompt=user_prompt, data=data)
    elif intent == "regression":
        result = regress(prompt=user_prompt, data=data)
    elif intent == "compare":
        result = comparison_tool(prompt=user_prompt, data=data)
    elif intent == "plot":
        result = plot(prompt=user_prompt, data=data, geojson=geojson)
    elif intent == "region analysis":
        result = region_analysis(prompt=user_prompt, data=data, geojson=geojson)
    elif intent == "forecast":
        result = forecast(prompt=user_prompt, data=data)
    elif intent == "categorical":
        result = categorical_tool(prompt=user_prompt, data=data)
    else:
        raise ValueError("Feature is not available")

    print(f"[DEBUG] Final result type: {type(result)}")
    if isinstance(result, dict):
        print(f"[DEBUG] Result keys: {list(result.keys())}")
        
        if "llm_summary" not in result:
            try:
                result = summarize_with_llm(result, user_prompt)
                print("[DEBUG] Added LLM summary.")
            except Exception as e:
                print(f"[ERROR] LLM summarization failed: {str(e)}")

    return result

def explore(prompt: str = "", data: List[Dict] = []) -> Dict:
    eda = EDA()
    try:
        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip().str.lower()
        valid_columns = df.columns.tolist()

        extracted = extract_columns_from_prompt(prompt, valid_columns, intent="explore")
        columns = extracted.get("columns", [])

        if not columns:
            raise ValueError("No suitable column found from prompt.")

        column = columns[0]
        result = eda.run(df, column)

        if result["histogram"] is not None:
            # Numeric case
            summary_text = (
                f"Summary statistics for '{column}':\n"
                f"{pd.Series(result['summary']).to_string()}\n\n"
                f"Skewness: {result['skew_type']}\n"
                f"Gini coefficient: {result['gini']:.4f}\n"
                f"Histogram peak range: {result['histogram_peak_range']}"
            )

            return {
                "intent": "describe",
                "type": "numeric",
                "summary_text": summary_text,
                "summary": result.get("summary", {}),
                "histogram_peak_range": result.get("histogram_peak_range"),
                "skew_type": result.get("skew_type"),
                "gini": result.get("gini"),
                "outliers": result.get("outlier_summary", {}).get("values", []),
                "histogram_data": result.get("histogram", {}).get("data"),
                "histogram_layout": result.get("histogram", {}).get("layout"),
                "boxplot_data": result.get("boxplot", {}).get("data"),
                "boxplot_layout": result.get("boxplot", {}).get("layout"),
                "table": df[[column]].head().to_dict("records")
            }

        else:
            # Categorical case
            counts = result["summary"]["value_counts"]
            proportions = result["summary"]["proportions"]
            mode = result["summary"]["mode"]
            summary_text = (
                f"Category distribution for '{column}':\n"
                f"Mode: {mode}\n"
                f"Counts: {counts}\n"
                f"Proportions: {proportions}"
            )

            return {
                "intent": "describe",
                "type": "categorical",
                "summary_text": summary_text,
                "summary": result.get("summary", {}),
                "barplot_data": result.get("barplot", {}).get("data"),
                "barplot_layout": result.get("barplot", {}).get("layout"),
                "piechart_data": result.get("piechart", {}).get("data"),
                "piechart_layout": result.get("piechart", {}).get("layout"),
                "table": df[[column]].head().to_dict("records")
            }

    except Exception as e:
        return {
            "intent": "describe",
            "type": "error",
            "summary_text": f"Tool error: {str(e)}",
            "histogram_data": None,
            "histogram_layout": None,
            "boxplot_data": None,
            "boxplot_layout": None,
            "barplot_data": None,
            "barplot_layout": None,
            "piechart_data": None,
            "piechart_layout": None,
            "summary": {},
            "table": [],
            "outliers": []
        }



def categorical_tool(prompt: str, data: list[dict]) -> dict:
    df = pd.DataFrame(data)
    valid_columns = df.columns.tolist()

    # Extract columns from prompt
    extracted = extract_columns_from_prompt(prompt, valid_columns, intent="categorical")
    columns = (
        extracted.get("columns")
        or extracted.get("group", []) + extracted.get("value", [])
        or extracted.get("features", [])
    )

    if not columns:
        return {
            "intent": "categorical",
            "message": "No columns could be extracted from prompt.",
            "columns": [],
            "test_type": None,
            "interpretation": None,
            "plotly_data": None,
            "plotly_layout": None,
            "table": None,
            "posthoc_table": None,
            "raw_prompt": prompt,
            "raw_data": data
        }

    try:
        agent = Categorical()
        result = agent.run(df, prompt=prompt, columns=columns)

        posthoc = result.get("posthoc_table")
        if isinstance(posthoc, pd.DataFrame):
            posthoc = posthoc.to_dict(orient="records")  # Ensure serializable format

        test_type = result.get("test_type", "unknown")
        test_type_display = {
            "mcnemar": "McNemar Test",
            "proportion": "Proportion Test",
            "association": "Chi-squared Association Test",
            "goodness": "Goodness of Fit Test"
        }.get(test_type, test_type.title())

        return {
            "intent": "categorical",
            "columns": columns,
            "test_type_display": test_type_display,
            "interpretation": result.get("summary_text"),
            "plotly_data": result.get("plotly_data"),
            "plotly_layout": result.get("plotly_layout"),
            "table": result.get("table"),
            "posthoc_table": posthoc,
            "raw_prompt": prompt,
            "raw_data": data
        }

    except Exception as e:
        print(f"[categorical tool error] {e}")
        return {
            "intent": "categorical",
            "message": f"Tool error: {e}",
            "columns": columns,
            "plotly_data": None,
            "plotly_layout": None,
            "table": None,
            "posthoc_table": None,
            "interpretation": None,
            "test_type_display": None,
            "raw_prompt": prompt,
            "raw_data": data
        }

def comparison_tool(prompt: str, data: list[dict]) -> dict:
    df = pd.DataFrame(data)
    valid_columns = df.columns.tolist()

    extracted = extract_columns_from_prompt(prompt, valid_columns, intent="compare")
    columns = (
        extracted.get("columns") or
        extracted.get("group", []) + extracted.get("value", []) or
        extracted.get("features", [])
    )
    print(f"[DEBUG] Extracted columns for comparison: {columns}")
    if not columns:
        return {
            "intent": "compare",
            "message": "No columns could be extracted from prompt.",
            "plotly_data": None,
            "plotly_layout": None,
            "posthoc": None,
            "interpretation": None,
            "test_type": None,
            "columns": []
        }

    try:
        agent = Comparison()
        result = agent.run(df, prompt=prompt, columns=columns)
        return {
            "intent": "compare",
            "columns": columns,
            "interpretation": result.get("summary_text"),
            "test_type": result.get("test_type"),
            "plotly_data": result.get("plotly_data"),
            "plotly_layout": result.get("plotly_layout"),
            "posthoc": result.get("posthoc")
        }

    except Exception as e:
        return {
            "intent": "compare",
            "message": f"Tool error: {str(e)}",
            "plotly_data": None,
            "plotly_layout": None,
            "posthoc": None,
            "interpretation": None,
            "test_type": None,
            "columns": columns
        }

def forecast(prompt: str = "", data: List[Dict] = []) -> Dict:
    try:
        df = pd.DataFrame(data)
        df.columns = [str(col).strip().lower() for col in df.columns]
        valid_columns = df.columns.tolist()

        inferred = extract_columns_from_prompt(prompt, valid_columns, intent="forecast")
        date_list = inferred.get("date", [])
        value_list = inferred.get("value", [])
        periods = inferred.get("periods", [30])[0]

        if not date_list or not value_list:
            raise ValueError("Missing required date or value columns from prompt.")

        date_col = date_list[0]
        value_col = value_list[0]

        if date_col not in df.columns or value_col not in df.columns:
            raise ValueError(f"Extracted columns not found in dataset: {date_col}, {value_col}")

        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce")

        if isinstance(periods, str) and periods.isdigit():
            periods = int(periods)
        elif not isinstance(periods, int):
            periods = 30

        return Forecast().run(df, date_col, value_col, periods)

    except Exception as e:
        return {
            "intent": "forecast",
            "summary_text": f"Tool error: {str(e)}",
            "plotly_data": None,
            "plotly_layout": None,
            "table": None
        }

def plot(prompt: str = "", data: List[Dict] = [], geojson: Dict = None) -> Dict:
    try:
        # Load and sanitize dataframe
        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip()
        if df.empty:
            raise ValueError("Uploaded data is empty.")

        valid_columns = df.columns.tolist()
        print(f"[DEBUG] Valid columns: {valid_columns}")

        # Step 1: Detect chart type
        chart_type = infer_chart_type(prompt).strip().lower()
        print(f"[DEBUG] Inferred chart type: {chart_type}")
        if not chart_type:
            raise ValueError("Could not determine chart type from prompt.")

        # Step 2: Extract relevant columns from prompt
        parsed = extract_columns_from_prompt(prompt, valid_columns, chart_type=chart_type)
        columns = parsed.get("columns", [])
        print(f"[DEBUG] Extracted columns from prompt: {columns}")
        if not columns:
            raise ValueError("Could not infer any columns to plot from prompt.")

        # Step 3: Convert geojson to GeoDataFrame if present
        geo_df = None
        if geojson:
            try:
                geo_df = gpd.GeoDataFrame.from_features(geojson["features"])
                print(f"[DEBUG] geo_df loaded with {len(geo_df)} features. Columns: {list(geo_df.columns)}")
            except Exception as e:
                print(f"[WARN] Failed to parse geojson: {e}")

        # Step 4: Call Plot tool with geo_df only if needed
        plot_tool = Plot()
        if chart_type == "choropleth":
            result = plot_tool.run(df, prompt, columns, chart_type, geo_df=geo_df)
        else:
            result = plot_tool.run(df, prompt, columns, chart_type)

        # === DEBUG: Inspect result type ===
        print(f"[DEBUG] Type of result returned by Plot.run: {type(result)}")
        if not isinstance(result, dict):
            raise ValueError(f"Plot.run() returned unexpected type: {type(result)}")

        print(f"[DEBUG] Dict result keys: {list(result.keys())}")

        # Step 5: Ensure required keys and return
        result.setdefault("intent", "plot")
        result.setdefault("summary_text", None)
        return result

    except Exception as e:
        print(f"[DEBUG] Exception occurred in plot tool: {str(e)}")
        return {
            "intent": "plot",
            "summary_text": f"Tool error: {str(e)}",
            "plotly_data": None,
            "plotly_layout": None
        }

def regress(prompt: str = "", data: List[Dict] = []) -> Dict:
    agent=LinearRegression()
    try:
        # Load and sanitize dataframe
        df = pd.DataFrame(data)
        df.columns = df.columns.str.strip()

        # Infer target/features using the prompt parser
        parsed = extract_columns_from_prompt(prompt, df.columns.tolist(), intent="regression")
        target = parsed.get("target", [None])[0]
        features = parsed.get("features", [])

        if not target or not features:
            raise ValueError("Could not infer target or features from prompt.")

        result = agent.run(df, target, features)

        return {
            "intent": "regression",
            "summary_text": result.get("summary_text"),
            "plotly_data": result.get("plotly_data"),
            "plotly_layout": result.get("plotly_layout"),
            "table": result.get("table"),
            "heteroskedasticity_detected": result.get("heteroskedasticity_detected", False),
            "reset_misspecification_detected": result.get("reset_misspecification_detected", False),
            "vif_filtering_applied": result.get("vif_filtering_applied", False),
            "aic_selection_applied": result.get("aic_selection_applied", False),
            "interactions_added": result.get("interactions_added", False)
        }

    except Exception as e:
        return {
            "summary_text": f"Tool error: {str(e)}",
            "plotly_data": None,
            "plotly_layout": None,
            "table": None,
            "heteroskedasticity_detected": False,
            "reset_misspecification_detected": False,
            "vif_filtering_applied": False,
            "aic_selection_applied": False,
            "interactions_added": False
        }

def region_analysis(prompt: str = "", data: List[Dict] = [], geojson: Dict = None) -> Dict:
    try:

        df = pd.DataFrame(data)
        df.columns = [str(col).strip().lower() for col in df.columns]
        valid_columns = df.columns.tolist()

        # Extract columns via LLM
        inferred = extract_columns_from_prompt(prompt, valid_columns, intent="region")
        print("[DEBUG] Extracted columns from prompt:", inferred)

        region_list = inferred.get("region", [])
        value_list = inferred.get("value", [])
        date_list = inferred.get("date", [])
        raw_periods = inferred.get("periods", None)
        periods = raw_periods[0] if isinstance(raw_periods, list) and raw_periods else raw_periods

        if not region_list or not value_list:
            raise ValueError("Could not extract region and value columns from prompt.")

        region_col = region_list[0]
        value_col = value_list[0]
        date_col = date_list[0] if date_list else None

        for col in [region_col, value_col, date_col]:
            if col and col not in df.columns:
                raise ValueError(f"Extracted column not found in dataset: {col}")

        # Handle geojson input
        geo_df = None
        if geojson:
            try:
                geo_df = gpd.GeoDataFrame.from_features(geojson["features"])
                print(f"[DEBUG] geo_df loaded with {len(geo_df)} rows. Columns: {list(geo_df.columns)}")
            except Exception as gerr:
                print(f"[WARN] Failed to parse geojson: {gerr}")

        analyzer = RegionAnalysis()

        if date_col:
            result = analyzer.run_temporal_model(
                df,
                date_col=date_col,
                region_col=region_col,
                value_col=value_col,
                forecast_horizon=periods or 10
            )
            return {
                "intent": "regionforecast",
                "model_type": result.get("model_type"),
                "forecast_horizon": result.get("forecast_horizon"),
                "plotly_data": result.get("plotly_data", []),
                "plotly_layout": result.get("plotly_layout", {}),
                "plotly_frames": result.get("plotly_frames", []),
                "forecast_summary": result.get("forecast_summary", []),
                "metrics": {
                    "bic": result.get("bic"),
                    "sigma2": result.get("sigma2"),
                    "loglikelihood": result.get("loglikelihood"),
                    "mae": result.get("mae"),
                    "mse": result.get("mse"),
                    "rmse": result.get("rmse"),
                },
            }
        else:
            # Pass geo_df for spatial clustering (Gi*)
            result = analyzer.run(df, region_col=region_col, value_col=value_col, geo_df=geo_df)
            return {
                "intent": "region analysis",
                "plotly_data": result.get("plotly_data", []),
                "plotly_layout": result.get("plotly_layout", {}),
                "gi_star_table": result.get("gi_star_table", []),
                "message": "Gi* Getis-Ord regional analysis completed."
            }

    except Exception as e:
        logger.error(f"[MCP] Region analysis tool error: {e}")
        return {
            "intent": "region analysis",
            "message": f"Tool error: {str(e)}",
            "plotly_data": None,
            "plotly_layout": None,
            "hotcold_data": None,
            "hotcold_layout": None,
            "gi_star_table": None
        }

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=server_port,
        path="/data_analysis"
    )