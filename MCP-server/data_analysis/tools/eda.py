# tools/eda.py
import pandas as pd
import plotly.express as px
import numpy as np
import math
import json
from data_analysis.utils.encoder import NumpyEncoder  # Keep as-is assuming MCP context

class EDA:
    def run(self, df: pd.DataFrame, column: str) -> dict:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")

        if pd.api.types.is_numeric_dtype(df[column]):
            return self._describe_numeric(df, column)

        elif pd.api.types.is_object_dtype(df[column]) or pd.api.types.is_categorical_dtype(df[column]):
            return self._describe_categorical(df, column)

        else:
            raise TypeError(f"Column '{column}' must be numeric or categorical.")

    def _describe_numeric(self, df: pd.DataFrame, column: str) -> dict:
        summary = df[column].describe()
        Q1, Q3 = summary["25%"], summary["75%"]
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)][column]

        bin_count = max(1, int(math.ceil(np.sqrt(df[column].dropna().shape[0]))))

        hist = px.histogram(df, x=column, nbins=bin_count, title=f"Histogram of {column}", text_auto=".2s")
        hist.update_layout(xaxis_title=column)

        box = px.box(df, y=column, title=f"Box Plot of {column}", points="outliers")
        box.update_layout(yaxis_title=column)

        hist_dict = hist.to_plotly_json()
        box_dict = box.to_plotly_json()

        peak_range, skew_type = self.histogram_characteristics(df[column], bins=bin_count)
        gini = self.compute_gini(df[column])

        return {
            "summary": json.loads(json.dumps(summary.to_dict(), cls=NumpyEncoder)),
            "histogram": json.loads(json.dumps(hist_dict, cls=NumpyEncoder)),
            "boxplot": json.loads(json.dumps(box_dict, cls=NumpyEncoder)),
            "outliers": json.loads(json.dumps(outliers.tolist(), cls=NumpyEncoder)),
            "histogram_peak_range": peak_range,
            "skew_type": skew_type,
            "gini": gini,
            "outlier_summary": {
                "count": len(outliers),
                "values": json.loads(json.dumps(outliers.tolist(), cls=NumpyEncoder))
            }
        }

    def _describe_categorical(self, df: pd.DataFrame, column: str) -> dict:
        counts = df[column].value_counts(dropna=False)
        proportions = counts / counts.sum()
        mode = df[column].mode().iloc[0] if not df[column].mode().empty else None

        bar = px.bar(x=counts.index.astype(str), y=counts.values,
                     title=f"Category Counts: {column}",
                     labels={'x': column, 'y': "Count"})
        pie = px.pie(names=proportions.index.astype(str), values=proportions.values,
                     title=f"Category Proportions: {column}")

        return {
            "summary": {
                "value_counts": json.loads(json.dumps(counts.to_dict(), cls=NumpyEncoder)),
                "proportions": json.loads(json.dumps(proportions.round(4).to_dict(), cls=NumpyEncoder)),
                "mode": mode
            },
            "barplot": json.loads(json.dumps(bar.to_plotly_json(), cls=NumpyEncoder)),
            "piechart": json.loads(json.dumps(pie.to_plotly_json(), cls=NumpyEncoder)),
            "histogram": None,
            "boxplot": None,
            "outliers": None,
            "histogram_peak_range": None,
            "skew_type": None,
            "gini": None,
            "outlier_summary": None
        }

    def histogram_characteristics(self, series: pd.Series, bins: int):
        values = series.dropna()
        hist, bin_edges = np.histogram(values, bins=bins)
        peak_idx = np.argmax(hist)
        peak_range = (float(bin_edges[peak_idx]), float(bin_edges[peak_idx + 1]))

        skewness = values.skew()
        if skewness > 1:
            skew_type = "strongly right-skewed"
        elif skewness > 0.5:
            skew_type = "moderately right-skewed"
        elif skewness < -1:
            skew_type = "strongly left-skewed"
        elif skewness < -0.5:
            skew_type = "moderately left-skewed"
        else:
            skew_type = "approximately symmetric"

        return peak_range, skew_type

    def compute_gini(self, series: pd.Series) -> float:
        values = series.dropna().values
        n = len(values)
        if n == 0:
            return float("nan")
        mean = np.mean(values)
        if abs(mean) < 1e-5:
            return float("inf")
        diff_sum = np.abs(np.subtract.outer(values, values)).sum()
        return diff_sum / (2 * n**2 * mean)