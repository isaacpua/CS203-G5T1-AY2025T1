from langchain.schema import HumanMessage
from data_analysis.utils.llm import llm
llm = llm()

def classify_intent(prompt: str) -> str:
    """
    Use LLM to classify prompt as one of: 
    'regression', 'describe', 'compare', 'plot', 'region analysis', 'forecast', 'categorical', or 'unknown'
    """

    instruction = (
        "You are a classifier. Return only one word: "
        "regression, describe, compare, categorical, plot, region analysis, forecast, or unknown.\n\n"
        "Classify based on user intent:\n"
        "- regression: predicting one variable using others\n"
        "- describe: if the prompt includes the word 'describe', return intent = 'describe'; for numeric columns, provide summary statistics, outliers, histogram, boxplot; for categorical columns, provide frequency counts and bar chart\n"
        "- compare: test differences between numeric groups (e.g., t-test, ANOVA)\n"
        "- categorical: test differences or relationships between categorical variables (e.g., chi-square, McNemar, proportions)\n"
        "- plot: request for chart or visualization (e.g., bar chart, line chart). "
        "If the prompt contains keywords like 'plot', 'chart', 'graph', or 'visualize', classify it as 'plot'.\n"
        "- region analysis: classify as region analysis if the prompt mentions terms like "
        "'region analysis', 'regional hotspot', 'spatial forecast', 'STARIMA', 'spatial-temporal', or any mention of forecasting over regions or towns.\n"
        "- forecast: time series prediction based on date and value columns\n"
        "- unknown: none of the above\n\n"
        f"Question: {prompt}\n"
        "Answer:"
    )

    response = llm.invoke([HumanMessage(content=instruction)])
    return response.content.strip().lower()