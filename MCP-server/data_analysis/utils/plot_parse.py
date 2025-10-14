from data_analysis.utils.llm import llm
from langchain.schema import HumanMessage

def infer_chart_type(prompt: str) -> str:
    """
    Use LLM to infer chart type. Response must be one of:
    scatter, line, bar, histogram, box, pie
    """
    response = llm().invoke([
        HumanMessage(content=
            "You are a chart classifier. Given a user request, reply with only one word: "
            "scatter, line, bar, histogram, box, pie, candlestick, choropleth, or scatter_map.\n"
            "Examples:\n"
            "• 'plot salary vs age' → scatter\n"
            "• 'show revenue over time' → line\n"
            "• 'distribution of weight' → histogram\n"
            "• 'group sales by region' → bar\n"
            "• 'box plot of income by gender' → box\n"
            "• 'pie chart of department counts' → pie\n"
            "• 'stock prices with open high low close' → candlestick\n"
            "• 'map of average housing price by district' → choropleth\n"
            "• 'scatter map of restaurant sales across locations' → scatter_map\n"
            f"\nPrompt: {prompt}"
        )
    ])
    chart_type = response.content.strip().lower()
    print(f"Inferred chart type: {chart_type}")
    return chart_type