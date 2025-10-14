import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
import json
from data_analysis.utils.encoder import NumpyEncoder

class Plot:
    def run(self, df: pd.DataFrame, prompt: str, columns: list, chart_type: str, geo_df: gpd.GeoDataFrame = None):
        if not columns:
            raise ValueError("No valid columns found to plot.")

        # Default x and y selection
        x = columns[0]
        y = columns[1] if len(columns) > 1 else None

        df_plot = df.copy()
        fig = None

        # Generate chart
        if chart_type == "scatter" and x and y:
            fig = px.scatter(df_plot, x=x, y=y, title=f"Scatter Plot: {y} vs {x}")
            fig.update_layout(xaxis_title=x, yaxis_title=y)

        elif chart_type == "line":
            date_cols = [col for col in df.columns if col.lower() == "date"]
            print(f"[DEBUG] Detected date columns: {date_cols}")
    
            if date_cols:
                x = date_cols[0]
                y = next((col for col in columns if col != x), None)
    
            print(f"[DEBUG] x: {x}, y: {y}")
            print(f"[DEBUG] All columns: {df.columns.tolist()}")

            if not x or not y:
                raise ValueError("Line plot requires one date column and one value column.")

            df_plot[x] = df[x]
            fig = px.line(df_plot, x=x, y=y, title=f"Line Plot: {y} over {x}")
            fig.update_layout(xaxis_title=x, yaxis_title=y)

        elif chart_type == "bar" and len(columns) >= 2:
            # Determine which column is numeric and which is categorical
            numeric_col = next((col for col in columns if pd.api.types.is_numeric_dtype(df_plot[col])), None)
            categorical_col = next((col for col in columns if col != numeric_col), None)

            if not numeric_col or not categorical_col:
                raise ValueError("Bar chart requires one numeric and one categorical column.")

            x = categorical_col
            y = numeric_col

            df_clean = df_plot[[x, y]].dropna()
            df_clean[y] = pd.to_numeric(df_clean[y], errors='coerce')
            df_clean = df_clean.dropna()

            # Group and sum y by x if duplicates exist
            if df_clean.duplicated(subset=[x]).any():
                agg_df = df_clean.groupby(x)[y].sum().reset_index()
                fig = px.bar(agg_df, x=x, y=y, title=f"Bar Chart: Total {y} by {x}")
            else:
                fig = px.bar(df_clean, x=x, y=y, title=f"Bar Chart: {y} by {x}")

            fig.update_layout(xaxis_title=x, yaxis_title=y)

        elif chart_type == "histogram" and x:
            fig = px.histogram(df_plot, x=x, title=f"Histogram of {x}")
            fig.update_layout(xaxis_title=x, yaxis_title="Count")

        elif chart_type == "box":
            numeric_cols = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])]
            categorical_cols = [col for col in columns if col not in numeric_cols]

            if len(numeric_cols) >= 2 and not categorical_cols:
                # Side-by-side boxplots for multiple numeric columns
                df_long = pd.melt(df[numeric_cols], var_name="Group", value_name="Value")
                fig = px.box(df_long, x="Group", y="Value", title="Box Plot: Comparison")
                fig.update_layout(xaxis_title="Group", yaxis_title="Value")

            elif len(numeric_cols) == 1 and len(categorical_cols) == 1:
                # One numeric, one categorical
                value_col = numeric_cols[0]
                group_col = categorical_cols[0]
                df_clean = df[[group_col, value_col]].dropna()
                fig = px.box(df_clean, x=group_col, y=value_col, title=f"Box Plot: {value_col} by {group_col}")
                fig.update_layout(xaxis_title=group_col, yaxis_title=value_col)

            elif len(numeric_cols) == 1 and len(categorical_cols) > 1:
                # One numeric, multiple categorical (composite group)
                value_col = numeric_cols[0]
                df_plot["Group"] = df_plot[categorical_cols].astype(str).agg(" | ".join, axis=1)
                fig = px.box(df_plot, x="Group", y=value_col, title=f"Box Plot: {value_col} by group")
                fig.update_layout(xaxis_title="Group", yaxis_title=value_col)

            elif len(numeric_cols) == 1 and not categorical_cols:
                # Single numeric column
                value_col = numeric_cols[0]
                fig = px.box(df, y=value_col, title=f"Box Plot of {value_col}")
                fig.update_layout(xaxis_title="", yaxis_title=value_col)

            else:
                raise ValueError("Could not create a valid boxplot with the selected columns.")

        elif chart_type == "pie":
            if len(columns) == 1:
                # Count frequency of each category
                names_col = columns[0]
                if names_col not in df_plot.columns:
                    raise ValueError(f"Pie chart error: column '{names_col}' not found.")
                fig = px.pie(df_plot, names=names_col, title=f"Pie Chart: Distribution of {names_col}")

            elif len(columns) == 2:
                cat_col, num_col = columns[0], columns[1]

                if cat_col not in df_plot.columns or num_col not in df_plot.columns:
                    raise ValueError(f"Pie chart error: columns '{cat_col}' or '{num_col}' not found.")

                df_clean = df_plot[[cat_col, num_col]].dropna()
                df_clean[num_col] = pd.to_numeric(df_clean[num_col], errors='coerce')
                df_clean = df_clean.dropna()

                agg_df = df_clean.groupby(cat_col)[num_col].sum().reset_index()

                fig = px.pie(agg_df, names=cat_col, values=num_col,
                             title=f"Pie Chart: Total {num_col} by {cat_col}")

            else:
                raise ValueError("Pie chart requires 1 or 2 columns.")

        elif chart_type == "candlestick":
            required_cols = ["Date", "Open", "High", "Low", "Close"]

            missing = [col for col in required_cols if col not in df_plot.columns]
            if missing:
                raise ValueError(
                    f"Candlestick chart requires columns: {', '.join(required_cols)}. "
                    f"Missing: {', '.join(missing)}"
                )

            df_candle = df_plot.copy()
            df_candle["Date"] = pd.to_datetime(df_candle["Date"], dayfirst=True, errors="coerce")
            df_candle = df_candle.dropna(subset=required_cols)

            fig = go.Figure(data=[go.Candlestick(
                x=df_candle["Date"],
                open=df_candle["Open"],
                high=df_candle["High"],
                low=df_candle["Low"],
                close=df_candle["Close"]
            )])

            fig.update_layout(
                title="Candlestick Chart",
                xaxis_title="Date",
                yaxis_title="Price",
                xaxis_rangeslider_visible=False
            )

        elif chart_type == "choropleth":
            region_col = next(
                (col for col in df.columns if not pd.api.types.is_numeric_dtype(df[col])),
                None
            )
            value_col = next(
                (col for col in df.columns if col != region_col and pd.api.types.is_numeric_dtype(df[col])),
                None
            )

            if not region_col:
                raise ValueError("Could not identify a region column (e.g., district, town, area).")
            if not value_col:
                raise ValueError("Could not identify a numeric value column for choropleth analysis.")

            # Clean and preprocess
            df_clean = df.dropna(subset=[region_col, value_col]).copy()
            df_clean[region_col] = df_clean[region_col].astype(str).str.strip().str.title()
            df_clean[value_col] = pd.to_numeric(df_clean[value_col], errors='coerce')
            df_clean = df_clean.dropna(subset=[value_col])

            agg_df = df_clean.groupby(region_col)[value_col].mean().reset_index()
            agg_df = agg_df.rename(columns={region_col: "planning_area", value_col: "value"})

            # Load GeoJSON
            if geo_df is not None:
                planning_areas = geo_df.copy()
                print(f"[DEBUG] Using custom geo_df with {len(planning_areas)} rows.")
            else:
                geojson_path = "data_analysis/utils/district_and_planning_area.geojson"
                planning_areas = gpd.read_file(geojson_path)
                print(f"[DEBUG] Loaded default geojson from {geojson_path} with {len(planning_areas)} rows.")
                
            planning_areas['planning_area'] = planning_areas['planning_area'].astype(str).str.strip().str.title()

            # Merge spatial + data
            merged = pd.merge(planning_areas, agg_df, on="planning_area", how="left")

            # Plot map
            fig = px.choropleth_map(
                merged,
                geojson=merged.__geo_interface__,
                locations="planning_area",
                featureidkey="properties.planning_area",
                color="value",
                color_continuous_scale="Viridis",
                center={"lat": 1.35, "lon": 103.82},
                zoom=10,
                title="Mean Value by Region"
            )
            fig.update_layout(
                margin={"r": 0, "t": 40, "l": 0, "b": 40},
                height=700,
            )
        elif chart_type == "scatter_map":
            if not isinstance(columns, list):
                raise ValueError("Expected a list of relevant columns for scatter map.")

            lat_col = next((col for col in columns if "lat" in col.lower()), None)
            lon_col = next((col for col in columns if "lon" in col.lower() or "lng" in col.lower()), None)
            label_col = next((col for col in columns if col not in [lat_col, lon_col]), None)
            value_col = next(
                (col for col in columns if col not in [lat_col, lon_col, label_col] and pd.api.types.is_numeric_dtype(df[col])),
                None
            )

            if not lat_col or not lon_col:
                raise ValueError("Scatter map requires both latitude and longitude columns.")

            fig = px.scatter_mapbox(
                df,
                lat=lat_col,
                lon=lon_col,
                hover_name=label_col,
                size=value_col,
                color=value_col,
                color_continuous_scale="Viridis",
                zoom=10,
                title="Scatter Map"
            )
            fig.update_layout(mapbox_style="open-street-map")
            fig.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 40}, height=700,autosize=True)

        if fig is None:
            raise ValueError(f"Unsupported or incomplete input for chart type: {chart_type}")

        # Convert x values to ISO strings for frontend if x is datetime
        if chart_type != "scatter_map" and x:
            for trace in fig.data:
                if hasattr(trace, 'x') and trace.x is not None:
                    x_array = np.array(trace.x)
                    if np.issubdtype(x_array.dtype, np.datetime64):
                        trace.x = [str(pd.to_datetime(val)) if val is not None else None for val in trace.x]

        # Serialize with NumpyEncoder
        try:
            fig_dict = fig.to_plotly_json()
            data_output = json.loads(json.dumps(fig_dict["data"], cls=NumpyEncoder))
            layout_output = json.loads(json.dumps(fig_dict["layout"], cls=NumpyEncoder))
            print(f"[DEBUG] Returning plotly_data with {len(data_output)} traces for chart type: {chart_type}")
            print(f"[DEBUG] plotly_data is None? {data_output is None}")
            print(f"[DEBUG] plotly_layout is None? {layout_output is None}")
        except Exception as e:
            print(f"[DEBUG] Error during serialization: {e}")
            raise

        return {
            "intent": "plot",
            "plotly_data": data_output,
            "plotly_layout": layout_output
        }


