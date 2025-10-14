import pandas as pd
import geopandas as gpd
import plotly.express as px
from esda import G_Local
from libpysal.weights import Queen, KNN
import numpy as np
import datetime
from data_analysis.utils.encoder import NumpyEncoder
import json
from statsmodels.tsa.stattools import adfuller
from data_analysis.utils.starma_model import STARMA, STARIMA
from data_analysis.utils.stacf_stpacf import Stacf
from data_analysis.utils.stacf_stpacf import Stpacf
from data_analysis.utils.starma_utils import set_stationary

class RegionAnalysis:
    def __init__(self, geojson_path="data_analysis/utils/district_and_planning_area.geojson"):
        self.geojson_path = geojson_path
        self.planning_areas = gpd.read_file(geojson_path)
        self.planning_areas['planning_area'] = (
            self.planning_areas['planning_area']
            .astype(str).str.strip().str.title()
        )

    def run(self, df: pd.DataFrame, region_col=None, value_col=None, geo_df=None):
        # Use custom geo_df if provided; otherwise use default
        if geo_df is not None:
            print(f"[DEBUG] Custom GeoDataFrame received with {len(geo_df)} rows and columns: {list(geo_df.columns)}")
            planning_areas = geo_df
        else:
            print("[DEBUG] Using default planning area GeoDataFrame from file")
            planning_areas = self.planning_areas

        # Clean region column
        df = df.dropna(subset=[region_col]).copy()
        df[region_col] = df[region_col].astype(str).str.strip().str.title()

        # Clean value column
        df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
        df = df.dropna(subset=[value_col])

        # Group and rename in one go
        agg_df = (
            df.groupby(region_col, as_index=False)[value_col]
            .mean()
            .rename(columns={region_col: "planning_area", value_col: "value"})
        )

        # Merge with spatial data
        merged = pd.merge(planning_areas, agg_df, on="planning_area", how="left")

        # --- Gi* test ---
        try:
            # Use only regions with values
            gdf = merged.dropna(subset=["value"]).reset_index(drop=True)

            # Create spatial weight matrix using Queen contiguity
            w = Queen.from_dataframe(gdf)

            # Identify isolated areas (no neighbors)
            no_neighbors = [i for i, neighbors in w.neighbors.items() if len(neighbors) == 0]

            if no_neighbors:
                print(f"Isolated regions detected: {no_neighbors}")
                # Apply KNN to those areas only
                knn = KNN.from_dataframe(gdf, k=1)
                for i in no_neighbors:
                    w.neighbors[i] = knn.neighbors[i]
                    w.weights[i] = knn.weights[i]

            # Run Local Gi* (Getis-Ord)
            gi = G_Local(gdf["value"], w)
            gdf["gi_zscore"] = gi.Zs
            gdf["gi_pvalue"] = gi.p_sim

            # Classify each region based on z and p
            def classify_spot(z, p):
                if p < 0.05:
                    return "Hotspot" if z > 0 else "Coldspot"
                return "Not Significant"

            gdf["spot_type"] = gdf.apply(lambda row: classify_spot(row["gi_zscore"], row["gi_pvalue"]), axis=1)

            # Merge Gi* results into the full GeoDF
            merged = merged.merge(
                gdf[["planning_area", "gi_zscore", "gi_pvalue", "spot_type"]],
                on="planning_area", how="left"
            )

            # Extract only statistically significant clusters
            gi_star_table = gdf.loc[
                gdf["spot_type"].isin(["Hotspot", "Coldspot"]),
                ["planning_area", "gi_zscore", "gi_pvalue", "spot_type"]
            ].to_dict("records")

        except Exception as e:
            print(f"Gi* test failed: {e}")
            gi_star_table = None

        # --- Plot Choropleth ---
        fig = px.choropleth_map(
            merged,
            geojson=merged.__geo_interface__,
            locations="planning_area",
            featureidkey="properties.planning_area",
            color="value",
            color_continuous_scale="Viridis",
            center={"lat": 1.35, "lon": 103.82},
            zoom=10,
            title="Mean Value by Town"
        )

        fig.update_layout(
            margin={"r": 0, "t": 40, "l": 0, "b": 40},
            height=700,
        )

        # Serialize Plotly figure
        fig_dict = fig.to_plotly_json()

        return {
            "intent": "regionplot",
            "plotly_data": json.loads(json.dumps(fig_dict["data"], cls=NumpyEncoder)),
            "plotly_layout": json.loads(json.dumps(fig_dict["layout"], cls=NumpyEncoder)),
            "gi_star_table": gi_star_table,
            "message": "Generated regional plot and performed Gi* test."
        }
    
    def run_temporal_model(self, df, date_col=None, region_col=None, value_col=None, forecast_horizon=10, geo_df=None):
        # === 1. Data Preparation ===
        df = df[[date_col, region_col, value_col]].dropna()
        df[region_col] = df[region_col].astype(str).str.strip().str.title()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(by=[date_col, region_col])

        pivoted_df = df.pivot(index=date_col, columns=region_col, values=value_col).dropna()
        ts_matrix = pivoted_df.to_numpy()
        region_names = pivoted_df.columns.tolist()
        last_date = pivoted_df.index[-1]

        # === Choose geo data ===
        if geo_df is not None:
            planning_areas = geo_df.copy()
            print(f"[DEBUG] Using custom geo_df with {len(planning_areas)} rows.")
        else:
            planning_areas = self.planning_areas
            print(f"[DEBUG] Using default planning_areas with {len(planning_areas)} rows.")

        planning_areas["planning_area"] = planning_areas["planning_area"].astype(str).str.strip().str.title()

        # Filter for matching regions
        regions = df[region_col].unique()
        gdf = planning_areas[planning_areas["planning_area"].isin(regions)].reset_index(drop=True)

        # === Build weight matrix ===
        w = Queen.from_dataframe(gdf, use_index=False)
        
        # Identify islands (regions with no neighbors)
        islands = w.islands
        if islands:
            print(f"[DEBUG] Found isolated regions (no neighbors): {islands}")
            # Build KNN matrix (e.g., k=1) as fallback
            knn = KNN.from_dataframe(gdf, k=1)
            for i in islands:
                w.neighbors[i] = knn.neighbors[i]
                w.weights[i] = knn.weights[i]

        # === Build spatial weight matrix (as numpy) ===
        wa_matrices = [w.full()[0]]

        # === 2. Stationarity Check (ADF) ===
        max_diff = 2
        d_orders = []
        for i in range(ts_matrix.shape[1]):
            d = 0
            for test_d in range(max_diff + 1):
                series = ts_matrix[:, i]
                test_series = np.diff(series, n=test_d) if test_d > 0 else series
                pval = adfuller(test_series)[1]
                if pval < 0.05:
                    d = test_d
                    break
            d_orders.append(d)

        max_d = max(d_orders)
        model_type = "STARIMA" if max_d > 0 else "STARMA"
        d_order = [max_d]

        # === 3. Identify AR (p) ===
        t_lags = ts_matrix.shape[0] - 1
        stpacf = Stpacf(ts_matrix, wa_matrices, t_lags).estimate()

        def infer_p(stpacf_matrix):
            magnitudes = [max(abs(v) for v in row) for row in stpacf_matrix]
            return int(np.argmax(magnitudes[1:]) + 1) if len(magnitudes) > 1 else 1

        p = infer_p(stpacf)

        # === 4. Iterative MA Order (q) Selection ===
        best_bic = np.inf
        best_q = 0
        best_model = None

        for q in range(3):  # Try q=0,1,2
            model = (STARIMA if model_type == "STARIMA" else STARMA)(
                p=p, d=d_order, q=q, ts_matrix=ts_matrix, wa_matrices=wa_matrices
            )
            model.fit()
            current_bic = model.bic()

            if current_bic < best_bic:
                best_bic = current_bic
                best_q = q
                best_model = model

        q = best_q
        model = best_model
        print(f"[INFO] Selected Model: {model_type}(p={p}, d={d_order}, q={q}), BIC={float(best_bic):.2f}")

        # === 5. Forecasting ===
        forecast_values = model.predict(ts_matrix=model._ts_matrix, t_lags=forecast_horizon)

        if model_type == "STARIMA":
            last_actual = pivoted_df.iloc[-1].values
            forecast = np.cumsum(forecast_values, axis=0) + last_actual
        else:
            forecast = forecast_values

        # === 5.1 Accuracy Metrics ===
        from sklearn.metrics import mean_absolute_error, mean_squared_error
        actual = pivoted_df.iloc[-forecast.shape[0]:].to_numpy()

        mae = float(mean_absolute_error(actual, forecast))
        mse = float(mean_squared_error(actual, forecast))
        rmse = float(np.sqrt(mse))

        bic = float(model.get_model()["bic"])
        sigma2 = float(model.get_model()["sigma2"])
        llh = float(model.get_model()["llh"])

        # === 6. Visualization ===
        historical_df = pivoted_df.reset_index().melt(id_vars=date_col, var_name="region", value_name="forecast")
        historical_df["type"] = "Actual"
        forecast_df = pd.DataFrame(forecast, columns=region_names)
        forecast_df["date"] = pd.date_range(start=last_date + pd.offsets.MonthBegin(), periods=len(forecast_df), freq="MS")
        forecast_long = forecast_df.melt(id_vars="date", var_name="region", value_name="forecast")
        forecast_long["type"] = "Forecast"
        combined_df = pd.concat([historical_df.rename(columns={date_col: "date"}), forecast_long], ignore_index=True)
        combined_df["frame"] = combined_df["date"].dt.strftime("%Y-%m")
        # Include both actual and forecast in summary
        forecast_summary = combined_df[["date", "region", "forecast", "type"]].copy()
        forecast_summary["date"] = forecast_summary["date"].dt.strftime("%Y-%m-%d")
        forecast_summary = forecast_summary.to_dict(orient="records")
        with open(self.geojson_path, "r") as f:
            geojson_data = json.load(f)

        fig = px.choropleth_mapbox(
            combined_df,
            geojson=geojson_data,
            featureidkey="properties.planning_area",
            locations="region",
            color="forecast",
            animation_frame="frame",
            mapbox_style="carto-positron",
            center={"lat": 1.3521, "lon": 103.8198},
            zoom=9,
            title="Actual and Forecasted Values by Planning Area",
            hover_name="type"
        )
        fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0}, height=700)
        fig_dict = fig.to_plotly_json()
        serialized_fig = {
            "plotly_data": json.loads(json.dumps(fig_dict["data"], cls=NumpyEncoder)),
            "plotly_layout": json.loads(json.dumps(fig_dict["layout"], cls=NumpyEncoder)),
            "plotly_frames": json.loads(json.dumps(fig_dict.get("frames", []), cls=NumpyEncoder))
        }

        # === 7. Output ===
        return {
            "intent": "regionforecast",
            "model_type": model_type,
            "forecast_horizon": forecast_horizon,
            "forecast_summary": forecast_summary,  # updated version includes both Actual & Forecast
            "plotly_data": serialized_fig["plotly_data"],
            "plotly_layout": serialized_fig["plotly_layout"],
            "plotly_frames": serialized_fig["plotly_frames"],
            "bic": bic,
            "sigma2": sigma2,
            "loglikelihood": llh,
            "mae": mae,
            "mse": mse,
            "rmse": rmse,
        }
