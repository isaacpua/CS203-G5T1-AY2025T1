# tools/regression.py
import pandas as pd
import plotly.graph_objects as go
from numpy.polynomial.polynomial import polyfit
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, linear_reset
from statsmodels.stats.outliers_influence import variance_inflation_factor
import itertools
import json
import numpy as np
from data_analysis.utils.encoder import NumpyEncoder
from typing import Union, List

class LinearRegression:
    def run(self, df, target, features):
        vif_filtering_applied = False
        aic_selection_applied = False
        interactions_added = False

        def calculate_vif(X_df):
            if X_df.shape[1] == 0:
                return pd.DataFrame(columns=["feature", "VIF"])
            vif_data = pd.DataFrame()
            vif_data["feature"] = X_df.columns
            vif_data["VIF"] = [variance_inflation_factor(X_df.values, i) for i in range(X_df.shape[1])]
            return vif_data

        def backward_aic_selection(X, y):
            current_features = list(X.columns)
            best_model = sm.OLS(y, X).fit()
            best_aic = best_model.aic
            while True:
                aic_scores = []
                for var in current_features:
                    if var == "const":
                        continue
                    try_vars = [v for v in current_features if v != var]
                    model_try = sm.OLS(y, X[try_vars]).fit()
                    aic_scores.append((model_try.aic, var, model_try))
                best_candidate = min(aic_scores, key=lambda x: x[0])
                if best_candidate[0] < best_aic:
                    best_aic = best_candidate[0]
                    best_model = best_candidate[2]
                    current_features.remove(best_candidate[1])
                else:
                    break
            return X[current_features], best_model

        # 1. Remove outliers
        Q1 = df[target].quantile(0.25)
        Q3 = df[target].quantile(0.75)
        IQR = Q3 - Q1
        df = df[(df[target] >= Q1 - 1.5 * IQR) & (df[target] <= Q3 + 1.5 * IQR)]

        # 2. Prepare data
        X = df[features].copy()

        # Encode binary categorical features
        for col in X.columns:
            if X[col].dtype == "object" or X[col].dtype.name == "category":
                num_unique = X[col].nunique(dropna=True)
                if num_unique == 2:
                    X[col] = X[col].astype("category").cat.codes
                else:
                    raise ValueError(f"Feature column '{col}' is non-numeric and not binary (has {num_unique} unique values).")

        # Convert to numeric just in case (e.g., mixed types)
        X = X.apply(pd.to_numeric, errors="coerce")
        y = pd.to_numeric(df[target], errors="coerce")

        # Align and drop missing
        X_sm = sm.add_constant(X).dropna()
        y = y.loc[X_sm.index]

        # Fit base model
        base_model = sm.OLS(y, X_sm).fit()
        best_aic = base_model.aic

        # 3. Heteroskedasticity (Breusch–Pagan)
        bp_stat, bp_pval, _, _ = het_breuschpagan(base_model.resid, base_model.model.exog)
        hetero_used = bp_pval < 0.05
        if hetero_used:
            base_model = sm.OLS(y, X_sm).fit(cov_type="HC3")
            best_aic = base_model.aic

        # 4. ramsey reset test with polynomial terms
        reset_misspec = False
        print("[DEBUG] Before Ramsey RESET:")
        print(f"  X_sm shape: {X_sm.shape}")
        print(f"  Columns: {list(X_sm.columns)}")
        print(f"  Params: {len(base_model.params)}")
        print(f"  AIC: {base_model.aic}")

        for power in range(2, 5):
            reset_result = linear_reset(base_model, power=power, test_type='fitted', use_f=False)
            if reset_result.pvalue < 0.05:
                reset_misspec = True
                print(f"[DEBUG] Ramsey RESET p-value for power {power}: {reset_result.pvalue:.4f} (model misspecified)")

                # Add polynomial terms up to the detected degree
                for p in range(2, power + 1):
                    for f in features:
                        col = f"{f}__pow{p}"
                        if col not in X_sm.columns:
                            X_sm[col] = X_sm[f] ** p
                            print(f"[DEBUG] Added column: {col}")

                # Clean and align before refitting
                X_sm = X_sm.dropna(axis=1, how="any")
                X_sm = X_sm.dropna()
                y = y.loc[X_sm.index]

                # Refit safely
                updated_model = sm.OLS(y, X_sm).fit()
                print("[DEBUG] After Ramsey RESET refit:")
                print(f"  X_sm shape: {X_sm.shape}")
                print(f"  Columns: {list(X_sm.columns)}")
                print(f"  Params: {len(updated_model.params)}")
                print(f"  AIC: {updated_model.aic}")

                if updated_model.aic < best_aic:
                    base_model = updated_model
                    best_aic = updated_model.aic
                    print("[DEBUG] Updated base_model with Ramsey-improved model")

                break  # stop after first significant RESET result
        print("[DEBUG] base_model params before interaction terms:")
        for name, coef in base_model.params.items():
            print(f"  {name}: {coef:.4f}")

        # 5. Interaction terms
        X_test = X_sm.copy()
        for f1, f2 in itertools.combinations(features, 2):
            col = f"{f1}__x__{f2}"
            X_test[col] = X_sm[f1] * X_sm[f2]

        X_test = X_test.dropna()
        y_test = y.loc[X_test.index]
        model_test = sm.OLS(y_test, X_test).fit()

        print("[DEBUG] interaction model params:")
        for name, coef in model_test.params.items():
            print(f"  {name}: {coef:.4f}")
        print(f"[DEBUG] interaction model AIC: {model_test.aic:.4f}")
        print(f"[DEBUG] base_model AIC before interaction: {best_aic:.4f}")

        if model_test.aic < best_aic:
            X_sm = X_test
            y = y_test
            base_model = model_test
            best_aic = model_test.aic
            interactions_added = True
            print("[DEBUG] base_model updated with interaction model")
            for name, coef in base_model.params.items():
                print(f"  {name}: {coef:.4f}")

        # 6. VIF filtering
        X_vif = X_sm.drop(columns=["const"], errors="ignore")

        if X_vif.shape[1] > 1:
            print("[DEBUG] base_model params before VIF filtering:")
            for name, coef in base_model.params.items():
                print(f"  {name}: {coef:.4f}")

            try:
                vif_df = calculate_vif(X_vif)
                vif_df = vif_df.replace([np.inf, -np.inf], np.nan).dropna()
                high_vif_cols = vif_df[vif_df["VIF"] > 10]["feature"].tolist()

                print(f"[DEBUG] VIF values:\n{vif_df.to_string(index=False)}")
                print(f"[DEBUG] High VIF columns to drop: {high_vif_cols}")

                if high_vif_cols:
                    X_test = X_sm.drop(columns=high_vif_cols)
                    X_test = X_test.dropna()
                    y_test = y.loc[X_test.index]
                    model_test = sm.OLS(y_test, X_test).fit()

                    print(f"[DEBUG] model AIC before VIF filtering: {best_aic:.4f}")
                    print(f"[DEBUG] model AIC after VIF filtering: {model_test.aic:.4f}")

                    if model_test.aic < best_aic:
                        X_sm = X_test
                        y = y_test
                        base_model = model_test
                        best_aic = model_test.aic
                        vif_filtering_applied = True

                        print("[DEBUG] base_model updated after VIF filtering:")
                        for name, coef in base_model.params.items():
                            print(f"  {name}: {coef:.4f}")

            except Exception as e:
                print(f"[VIF WARNING] Skipping VIF filtering due to error: {e}")

        # 7. Backward AIC selection
        if X_sm.shape[1] > 1:
            X_test, model_test = backward_aic_selection(X_sm, y)
            X_test = X_test.dropna()
            y_test = y.loc[X_test.index]
            model_test = sm.OLS(y_test, X_test).fit()
            if model_test.aic < best_aic:
                X_sm = X_test
                y = y_test
                base_model = model_test
                best_aic = model_test.aic
                aic_selection_applied = True

        X_sm = X_sm.loc[base_model.fittedvalues.index]
        y_pred = base_model.fittedvalues

        try:
            summary_text = base_model.summary().as_text()
            coeff_dict = base_model.params.to_dict()
        except Exception as e:
            summary_text = f"[WARNING] Could not generate model summary: {e}"
            coeff_dict = base_model.params.to_dict()

        fig = None
        if len(features) == 1:
            x = features[0]
            df_plot = pd.DataFrame({x: X[x], "Actual": y, "Predicted": y_pred})
            b, m = polyfit(df_plot[x], df_plot["Actual"], 1)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_plot[x], y=df_plot["Actual"], mode="markers", name="Actual"))
            fig.add_trace(go.Scatter(x=df_plot[x], y=m * df_plot[x] + b, mode="lines", name="Trendline"))
            fig.update_layout(
                title=f"{target} by {x}",
                xaxis_title=x,
                yaxis_title=target
            )
        elif len(features) == 2:
            x1, x2 = features
            df_plot = df[[x1, x2]].copy()
            df_plot["Predicted"] = y_pred
            fig = go.Figure(data=[
                go.Scatter3d(x=df_plot[x1], y=df_plot[x2], z=y, mode="markers", name="Actual"),
                go.Scatter3d(x=df_plot[x1], y=df_plot[x2], z=df_plot["Predicted"], mode="markers", marker=dict(color="red"), name="Predicted")
            ])
            fig.update_layout(
                title=f"{target} by {x1} and {x2}",
                scene=dict(
                    xaxis_title=x1,
                    yaxis_title=x2,
                    zaxis_title=target,
                    aspectmode="manual",  # or "cube" / "data"
                    aspectratio=dict(x=1.2, y=1.2, z=0.8)  # adjust as needed
                ),
                margin=dict(l=0, r=0, b=0, t=40),
                height=700,
                width=1000
            )

        result = {
            "heteroskedasticity_detected": hetero_used,
            "summary_text": summary_text,
            "vif_filtering_applied": vif_filtering_applied,
            "aic_selection_applied": aic_selection_applied,
            "interactions_added": interactions_added,
        }

        if fig:
            fig_dict = fig.to_plotly_json()
            result["plotly_data"] = json.loads(json.dumps(fig_dict["data"], cls=NumpyEncoder))
            result["plotly_layout"] = json.loads(json.dumps(fig_dict["layout"], cls=NumpyEncoder))

        return result
