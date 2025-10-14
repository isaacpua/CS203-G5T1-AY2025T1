import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import chi2_contingency, chisquare, chi2, norm, binomtest
from statsmodels.stats.proportion import proportions_ztest
from data_analysis.utils.categorical_parse import extract_categorical_test_info
import json
from data_analysis.utils.encoder import NumpyEncoder

class Categorical:
    def run(self, df: pd.DataFrame, prompt: str, columns: list) -> dict:
        df.columns = df.columns.str.strip().str.lower()
        columns = [c.strip().lower() for c in columns]

        if any(col not in df.columns for col in columns):
            raise ValueError(f"One or more columns not found in DataFrame: {columns}")

        info = extract_categorical_test_info(prompt, columns, df)
        test_type = info.get("test_type", "").strip().lower()
        selected = info.get("columns", columns)

        if test_type == "mcnemar":
            if len(selected) != 2:
                raise ValueError("McNemar test requires exactly two binary columns.")
            return self.mcnemar_test(df, selected)

        elif test_type == "goodness":
            return self.goodness_of_fit(df)

        elif test_type == "proportion":
            if len(selected) != 2:
                raise ValueError("Proportion test requires two columns: one group and one binary outcome.")
            return self.proportion_test(df, selected)

        elif test_type == "association":
            if len(selected) == 2:
                col1, col2 = selected

                # Detect a "Count" column (case-insensitive)
                count_col = next((c for c in df.columns if c.lower() == "count"), None)

                if count_col:
                    print("Case 1: long format with Count column → pivoting to wide format")
                    pivot_df = df.pivot_table(index=col1,
                                              columns=col2,
                                              values=count_col,
                                              aggfunc="sum",
                                              fill_value=0)
                    wide_columns = [pivot_df.index.name] + list(pivot_df.columns)
                    return self.association_test(pivot_df.reset_index(), wide_columns)
                else:
                    raise ValueError("Raw long format without Count column is not supported.")

            elif len(selected) > 2:
                print("Case 2: wide format detected with one categorical and multiple numeric columns")
                for col in selected:
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        row_label = col
                        numeric_cols = [c for c in selected if c != col]
                        if all(pd.api.types.is_numeric_dtype(df[c]) for c in numeric_cols):
                            return self.association_test(df, [row_label] + numeric_cols)

            raise ValueError("Chi-squared test requires either two categorical columns (with Count) or a wide-format table.")

        else:
            raise ValueError(f"Unknown test_type: '{test_type}'")

            return {
                "summary_text": result.get("summary_text") or result.get("interpretation"),
                "test_type": "association",
                "plotly_data": result.get("plotly_data"),
                "plotly_layout": result.get("plotly_layout"),
                "table": result.get("table")
            }


    def association_test(self, df, columns):
        if not columns or len(columns) < 2:
            raise ValueError("Association test requires at least two columns.")

        # --- CASE 1: long format ---
        if all(pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]) for col in columns[:2]):
            col_a, col_b = columns[:2]
            ctab = pd.crosstab(df[col_a], df[col_b])
        else:
            # --- CASE 2: wide format ---
            if len(columns) <= 2:
                raise ValueError("Association test requires wide-format data with one categorical and multiple numeric columns.")
            melted = df.melt(id_vars=columns[0], var_name="__CategoryB__", value_name="__Count__")
            melted["__Count__"] = pd.to_numeric(melted["__Count__"], errors="coerce").fillna(0).astype(int)
            df_expanded = melted.loc[melted.index.repeat(melted["__Count__"])].reset_index(drop=True)
            df_expanded = df_expanded[[columns[0], "__CategoryB__"]]
            df_expanded.columns = ["__A__", "__B__"]
            ctab = pd.crosstab(df_expanded["__A__"], df_expanded["__B__"])

        # Chi-squared test
        chi2_stat, p, dof, expected = chi2_contingency(ctab, correction=False)

        # Heatmap
        fig = go.Figure(data=go.Heatmap(
            z=ctab.values,
            x=ctab.columns,
            y=ctab.index,
            colorscale="Blues",
            text=ctab.values,
            texttemplate="%{text}",
            showscale=False
        ))
        fig.update_layout(title="Association Heatmap", xaxis_title="Category B", yaxis_title="Category A")
        fig_dict = fig.to_plotly_json()
        plotly_data = json.loads(json.dumps(fig_dict["data"], cls=NumpyEncoder))
        plotly_layout = json.loads(json.dumps(fig_dict["layout"], cls=NumpyEncoder))

        # Always compute adjusted standardized residuals
        observed = ctab.values
        total = observed.sum()
        row_totals = observed.sum(axis=1, keepdims=True)
        col_totals = observed.sum(axis=0, keepdims=True)
        adj_std_resid = (observed - expected) / np.sqrt(
            expected * (1 - row_totals / total) * (1 - col_totals / total)
        )

        significance = []
        for r in adj_std_resid.flatten():
            abs_r = abs(r)
            if abs_r >= norm.ppf(1 - 0.0001 / 2):
                significance.append("****")
            elif abs_r >= norm.ppf(1 - 0.001 / 2):
                significance.append("***")
            elif abs_r >= norm.ppf(1 - 0.01 / 2):
                significance.append("**")
            elif abs_r >= norm.ppf(1 - 0.05 / 2):
                significance.append("*")
            elif abs_r >= norm.ppf(1 - 0.10 / 2):
                significance.append(".")
            else:
                significance.append("n.s.")

        posthoc_table = pd.DataFrame({
            "Category": np.repeat(ctab.index, ctab.shape[1]),
            "Label": np.tile(ctab.columns, ctab.shape[0]),
            "Observed": observed.flatten(),
            "Expected": expected.flatten(),
            "StdResidual": np.round(adj_std_resid.flatten(), 2),
            "Significance": significance
        })

        return {
            "summary_text": f"Chi-squared: {chi2_stat:.4f}, p = {p:.4f}, df = {dof}. " +
                            ("Variables are associated." if p < 0.05 else "No significant association."),
            "test_type": "association",
            "plotly_data": plotly_data,
            "plotly_layout": plotly_layout,
            "table": ctab.reset_index().to_dict("records"),
            "posthoc_table": posthoc_table
        }

    def mcnemar_test(self, df, columns):
        # Step 0: Preprocess to clean column values
        for col in columns:
            df[col] = df[col].astype(str).str.strip().str.lower()

        # Optional: Map 1/0 and yes/no variants
        mapping = {
            "1": "yes", "0": "no",
            "true": "yes", "false": "no",
            "y": "yes", "n": "no"
        }
        for col in columns:
            df[col] = df[col].replace(mapping)

        # Keep only rows with valid binary values
        df = df[df[columns[0]].isin(["yes", "no"]) & df[columns[1]].isin(["yes", "no"])]

        # Step 1: Create 2×2 contingency table with binary values
        tbl = pd.crosstab(df[columns[0]], df[columns[1]])

        # Ensure consistent order and fill missing cells
        labels = sorted(set(df[columns[0]].unique()) | set(df[columns[1]].unique()))
        tbl = tbl.reindex(index=labels, columns=labels, fill_value=0)

        if tbl.shape != (2, 2):
            raise ValueError("McNemar test requires a 2×2 table with binary values.")

        # Step 2: Extract discordant counts
        b = tbl.iloc[0, 1]  # Yes → No
        c = tbl.iloc[1, 0]  # No → Yes
        discordant = b + c

        # Step 3: Choose test based on discordant pair count
        if discordant <= 10:
            # Exact binomial test
            stat = None
            p = binomtest(min(b, c), n=discordant, p=0.5, alternative="two-sided").pvalue
            method = "Exact binomial test"
        elif discordant <= 25:
            # McNemar with continuity correction
            stat = (abs(b - c) - 1)**2 / (discordant + 1e-9)
            p = 1 - chi2.cdf(stat, df=1)
            method = "McNemar test with continuity correction"
        else:
            # Standard McNemar test
            stat = (b - c)**2 / (discordant + 1e-9)
            p = 1 - chi2.cdf(stat, df=1)
            method = "Standard McNemar test"

        # Step 4: Create Plotly heatmap
        fig = go.Figure(data=go.Heatmap(
            z=tbl.values,
            x=tbl.columns,
            y=tbl.index,
            colorscale="Blues",
            text=tbl.values,
            texttemplate="%{text}",
            showscale=False
        ))
        fig.update_layout(
            title=f"2×2 Contingency Table ({method})",
            xaxis_title=columns[1],
            yaxis_title=columns[0]
        )

        fig_dict = fig.to_plotly_json()
        plotly_data = json.loads(json.dumps(fig_dict["data"], cls=NumpyEncoder))
        plotly_layout = json.loads(json.dumps(fig_dict["layout"], cls=NumpyEncoder))

        # Step 5: Construct interpretation summary
        if stat is None:
            stat_line = ""
        else:
            stat_line = f"Test statistic: {stat:.4f}\n"

        direction = ""
        if p < 0.05:
            if b > c:
                direction = "More responses changed from Yes to No."
            elif c > b:
                direction = "More responses changed from No to Yes."
            else:
                direction = "Equal number of Yes→No and No→Yes transitions."

        summary_text = (
            f"{method}\n"
            f"Discordant pairs (b + c): {discordant}\n"
            f"{stat_line}"
            f"p-value: {p:.4f}\n"
            f"{'Significant change observed.' if p < 0.05 else 'No significant change.'}\n"
            f"{direction}"
        )

        return {
            "summary_text": summary_text,
            "test_type": "mcnemar",
            "plotly_data": plotly_data,
            "plotly_layout": plotly_layout,
            "table": tbl.reset_index().to_dict("records"),
        }

    def goodness_of_fit(self, df):
        # Detect categorical column
        cat_col = next((col for col in df.columns if df[col].dtype == 'object'), None)
        if not cat_col:
            raise ValueError("No categorical column detected.")

        # Detect numeric columns
        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
        if len(numeric_cols) < 1:
            raise ValueError("No numeric columns found for observed counts.")
        observed_col = numeric_cols[0]
        expected_col = numeric_cols[1] if len(numeric_cols) > 1 else None

        # Prepare data
        observed = df[observed_col].values
        if expected_col:
            expected = df[expected_col].values
            expected = expected / expected.sum() * observed.sum()  # Normalize expected to match total observed
        else:
            expected = [sum(observed) / len(observed)] * len(observed)
        labels = df[cat_col].values

        # Run chi-squared test
        chi2_stat, p = chisquare(f_obs=observed, f_exp=expected)

        # Compute standardized residuals
        std_res = (observed - expected) / np.sqrt(expected)
        stars = []
        for r in std_res:
            abs_r = abs(r)
            if abs_r >= norm.ppf(1 - 0.0001 / 2):
                stars.append("****")
            elif abs_r >= norm.ppf(1 - 0.001 / 2):
                stars.append("***")
            elif abs_r >= norm.ppf(1 - 0.01 / 2):
                stars.append("**")
            elif abs_r >= norm.ppf(1 - 0.05 / 2):
                stars.append("*")
            elif abs_r >= norm.ppf(1 - 0.10 / 2):
                stars.append(".")
            else:
                stars.append("n.s.")

        # Create bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(x=labels, y=observed, name="Observed"))
        fig.add_trace(go.Bar(x=labels, y=expected, name="Expected"))
        fig.update_layout(
            title="Goodness-of-Fit Test: Observed vs Expected",
            barmode="group",
            xaxis_title=cat_col,
            yaxis_title="Count"
        )
        fig_dict = fig.to_plotly_json()
        plotly_data = json.loads(json.dumps(fig_dict["data"], cls=NumpyEncoder))
        plotly_layout = json.loads(json.dumps(fig_dict["layout"], cls=NumpyEncoder))

        # Construct post-hoc table
        posthoc_table = pd.DataFrame({
            cat_col: labels,
            "Observed": observed,
            "Expected": expected,
            "StdResidual": np.round(std_res, 2),
            "Significance": stars
        })

        return {
            "plotly_data": plotly_data,
            "plotly_layout": plotly_layout,
            "summary_text": f"GOF χ² = {chi2_stat:.4f}, p = {p:.4f}. " +
                            ("Differs from expected." if p < 0.05 else "No significant difference."),
            "test_type": "goodness",
            "posthoc_table": posthoc_table,
            "table": df.to_dict("records")
        }

    def proportion_test(self, df, columns):
        group_col, binary_col = columns
        grouped = df.groupby(group_col)[binary_col].value_counts().unstack().fillna(0)

        if grouped.shape[1] != 2:
            raise ValueError("Binary outcome required for proportion test.")

        # Normalize for proportions
        proportions = grouped.div(grouped.sum(axis=1), axis=0)

        # Plot
        fig = go.Figure()
        for outcome in proportions.columns:
            fig.add_trace(go.Bar(
                x=proportions.index,
                y=proportions[outcome],
                name=str(outcome)
            ))
        fig.update_layout(
            title="Proportion Comparison by Group (Stacked Bar)",
            yaxis_title="Proportion",
            barmode="stack"
        )

        # Z-test
        try:
            if grouped.shape[0] != 2:
                raise ValueError("Z-test is only supported for exactly two groups.")
            success = grouped.iloc[:, 1].values  # Assume 2nd column is "Yes"/"Success"
            nobs = grouped.sum(axis=1).values
            z_stat, pval = proportions_ztest(success, nobs)

            # Interpret direction
            group_names = grouped.index.tolist()
            rates = success / nobs
            if pval < 0.05:
                if rates[0] > rates[1]:
                    direction = f"{group_names[0]} has a higher proportion than {group_names[1]}."
                elif rates[1] > rates[0]:
                    direction = f"{group_names[1]} has a higher proportion than {group_names[0]}."
                else:
                    direction = "Both groups have equal proportions."
                summary = f"Z-test for two proportions: Z = {z_stat:.4f}, p = {pval:.4f}. Significant difference in proportions.\n{direction}"
            else:
                summary = f"Z-test for two proportions: Z = {z_stat:.4f}, p = {pval:.4f}. No significant difference."
        except Exception as e:
            summary = f"Could not perform z-test: {e}"

        # Encode plotly
        fig_dict = fig.to_plotly_json()
        plotly_data = json.loads(json.dumps(fig_dict["data"], cls=NumpyEncoder))
        plotly_layout = json.loads(json.dumps(fig_dict["layout"], cls=NumpyEncoder))

        return {
            "summary_text": summary,
            "test_type": "proportion",
            "plotly_data": plotly_data,
            "plotly_layout": plotly_layout,
            "table": df.to_dict("records")
        }
