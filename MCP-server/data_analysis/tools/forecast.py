import pandas as pd
import numpy as np
import json
from prophet import Prophet
import plotly.graph_objects as go
from data_analysis.utils.encoder import NumpyEncoder

class Forecast:
    def run(self, df: pd.DataFrame, date_col: str, value_col: str, periods: int = 30):
        # Step 1: Prepare data
        df = df[[date_col, value_col]].dropna()
        df = df.rename(columns={date_col: "ds", value_col: "y"})
        df["ds"] = pd.to_datetime(df["ds"], errors="coerce")
        df = df.dropna(subset=["ds", "y"])
        df["y"] = pd.to_numeric(df["y"], errors="coerce")

        # Step 2: Fit model
        model = Prophet()
        model.fit(df)

        # Step 3: Forecast
        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)

        # Step 4: Extract forecast data
        forecast_output = (
            forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
            .tail(periods)
            .rename(columns={
                "ds": "Date",
                "yhat": "Forecast",
                "yhat_lower": "Lower Bound",
                "yhat_upper": "Upper Bound"
            })
        )

        # Convert dates to string for JSON serialization
        forecast_output["Date"] = forecast_output["Date"].astype(str)

        # ✅ Use renamed column for delta
        delta = forecast_output["Forecast"].iloc[-1] - forecast_output["Forecast"].iloc[0]

        # ✅ Convert to tabular format (list of dictionaries)
        tabular_forecast = forecast_output.to_dict(orient="records")

        # Step 5: Plotly chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["ds"], y=df["y"], name="Actual"))
        fig.add_trace(go.Scatter(x=forecast["ds"], y=forecast["yhat"], name="Forecast"))
        fig.add_trace(go.Scatter(
            x=forecast["ds"],
            y=forecast["yhat_upper"],
            name="Upper Bound",
            line=dict(width=0),
            mode="lines",
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=forecast["ds"],
            y=forecast["yhat_lower"],
            name="Lower Bound",
            fill="tonexty",
            line=dict(width=0),
            mode="lines",
            fillcolor="rgba(0,100,80,0.2)",
            showlegend=False
        ))
        fig.update_layout(title="Forecast with Prophet", height=500)

        # Step 6: Interpretation
        delta = forecast_output["Forecast"].iloc[-1] - forecast_output["Forecast"].iloc[0]
        direction = "increasing" if delta > 0 else "decreasing" if delta < 0 else "stable"
        y_min = forecast_output["Forecast"].min()
        y_max = forecast_output["Forecast"].max()
        avg_ci_width = (forecast_output["Upper Bound"] - forecast_output["Lower Bound"]).mean()

        interpretation = (
            f"The forecast shows a {direction} trend over the next {periods} periods.\n"
            f"Forecasted values range from {y_min:.2f} to {y_max:.2f}.\n"
            f"Average uncertainty range (95% CI width): ±{avg_ci_width / 2:.2f}."
        )

        # Step 7: Serialize Plotly output
        #This trace thing actually works 
        for trace in fig.data:
            if hasattr(trace, 'x'):
                trace.x = [str(pd.to_datetime(x)) for x in trace.x]
        fig_dict = fig.to_plotly_json()
        data_output = json.loads(json.dumps(fig_dict["data"], cls=NumpyEncoder))
        layout_output = json.loads(json.dumps(fig_dict["layout"], cls=NumpyEncoder))

        return {
            "intent": "forecast",
            "plotly_data": data_output,
            "plotly_layout": layout_output,
            "forecast_table": tabular_forecast,
            "interpretation": interpretation
        }
