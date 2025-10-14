import pandas as pd
import numpy as np
from scipy.stats import ttest_ind, ttest_rel, levene, f_oneway, shapiro, wilcoxon, mannwhitneyu, kruskal
import scikit_posthocs as sp
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import plotly.express as px
import pingouin as pg
from data_analysis.utils.comparison_parse import extract_comparison_test_info
import json
from data_analysis.utils.encoder import NumpyEncoder

class Comparison:
    def run(self, df: pd.DataFrame, prompt: str, columns: list) -> dict:
        if any(col not in df.columns for col in columns):
            raise ValueError(f"One or more columns not found in DataFrame: {columns}")

        info = extract_comparison_test_info(prompt, columns, df)
        test_type = info.get("test_type", "").strip().lower()

        if test_type == "paired":
            if len(columns) != 2:
                raise ValueError("Paired t-test requires exactly 2 columns.")
            if not all(pd.api.types.is_numeric_dtype(df[col]) for col in columns):
                raise ValueError("Paired t-test requires two numeric columns.")
            return self._paired_ttest(df, columns[0], columns[1])

        elif test_type == "independent":
            if len(columns) != 2:
                raise ValueError("Independent t-test requires exactly 2 columns.")

            col1, col2 = columns

            is_num1 = pd.api.types.is_numeric_dtype(df[col1])
            is_num2 = pd.api.types.is_numeric_dtype(df[col2])

            # Ensure at least one numeric column
            if not (is_num1 or is_num2):
                raise ValueError("Independent t-test requires at least one numeric column.")

            # If one column is categorical, ensure it's binary
            if not is_num1:
                if df[col1].dropna().nunique() != 2:
                    raise ValueError(f"Categorical column '{col1}' must have exactly 2 unique values.")
            if not is_num2:
                if df[col2].dropna().nunique() != 2:
                    raise ValueError(f"Categorical column '{col2}' must have exactly 2 unique values.")

            # Unified handler (renamed to _independent_ttest)
            return self._independent_ttest(df, col1, col2)

        elif test_type == "anova":
            if len(columns) == 2:
                col1, col2 = columns
                if pd.api.types.is_numeric_dtype(df[col1]) and not pd.api.types.is_numeric_dtype(df[col2]):
                    num_col, group_col = col1, col2
                elif pd.api.types.is_numeric_dtype(df[col2]) and not pd.api.types.is_numeric_dtype(df[col1]):
                    num_col, group_col = col2, col1
                else:
                    raise ValueError("ANOVA with 2 columns requires one numeric and one categorical column.")

                if df[group_col].dropna().nunique() < 3:
                    raise ValueError(f"ANOVA requires at least 3 groups in '{group_col}'.")

                return self._anova_test(df, group_col=group_col, value_col=num_col)

            elif len(columns) >= 3:
                # All must be numeric columns
                for col in columns:
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        raise ValueError("All columns must be numeric for multi-column ANOVA.")

                # Drop rows with any missing values across selected numeric columns
                df_filtered = df[columns].dropna()

                # Convert to long format for standard ANOVA
                df_long = df_filtered.melt(var_name="group", value_name="value")
                return self._anova_test(df_long, group_col="group", value_col="value")

            else:
                raise ValueError("ANOVA requires at least two columns.")

        else:
            raise ValueError(f"Unsupported or unrecognized test_type: '{test_type}'")

    def _remove_outliers_iqr(self, series: pd.Series) -> pd.Series:
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        return series[(series >= Q1 - 1.5 * IQR) & (series <= Q3 + 1.5 * IQR)]

    def _paired_ttest(self, df: pd.DataFrame, col1: str, col2: str) -> dict:
        paired_df = df[[col1, col2]].dropna()
        paired_df["diff"] = paired_df[col1] - paired_df[col2]

        test_type = "Paired t-test"
        use_wilcoxon = False
        n = len(paired_df)

        # Normality check
        if n < 30:
            _, p_shapiro = shapiro(paired_df["diff"])
            if p_shapiro < 0.05:
                use_wilcoxon = True
                test_type = "Wilcoxon signed-rank test"
                normality_note = "Differences are not normally distributed (Shapiro-Wilk p < 0.05)."
            else:
                normality_note = "Differences are approximately normally distributed (Shapiro-Wilk p ≥ 0.05)."
        else:
            normality_note = "Sample size is large (n ≥ 30); normality assumed via Central Limit Theorem."

        # Run appropriate test
        if use_wilcoxon:
            stat, p_value = wilcoxon(paired_df[col1], paired_df[col2])
        else:
            stat, p_value = ttest_rel(paired_df[col1], paired_df[col2])

        mean_diff = paired_df["diff"].mean()

        # Directional interpretation
        if p_value < 0.05:
            if mean_diff > 0:
                direction = f"\nOn average, '{col1}' values are higher than '{col2}'."
            elif mean_diff < 0:
                direction = f"\nOn average, '{col2}' values are higher than '{col1}'."
            else:
                direction = "\nThe average difference is zero."
        else:
            direction = "\nNo directional conclusion due to lack of significance."

        df_value = n - 1 if not use_wilcoxon else "N/A"
        interpretation = (
            f"{test_type} between '{col1}' and '{col2}':\n"
            f"Test statistic = {stat:.4f}\n"
            f"Degrees of freedom = {df_value}\n"
            f"p-value        = {p_value:.4f}\n"
            f"Normality check: {normality_note}\n"
            f"{'Statistically significant difference (p < 0.05).' if p_value < 0.05 else 'No significant difference.'}"
            f"{direction}"
        )

        # Plot
        fig = px.box(paired_df, y="diff", title=f"{col1} vs {col2}")
        fig.update_layout(xaxis_title="", yaxis_title="Difference", template="plotly_white", boxmode="group")
        fig_dict = fig.to_plotly_json()

        return {
            "summary_text": interpretation,
            "test_type": test_type,
            "plotly_data": json.loads(json.dumps(fig_dict["data"], cls=NumpyEncoder)),
            "plotly_layout": json.loads(json.dumps(fig_dict["layout"], cls=NumpyEncoder)),
            "table": paired_df[[col1, col2, "diff"]].head().to_dict("records"),
            "posthoc": None
        }

    def _independent_ttest(self, df: pd.DataFrame, col1: str, col2: str, prompt: str = "") -> dict:
        df = df[[col1, col2]].dropna()

        is_col1_numeric = pd.api.types.is_numeric_dtype(df[col1])
        is_col2_numeric = pd.api.types.is_numeric_dtype(df[col2])

        if is_col1_numeric and is_col2_numeric:
            series1, series2 = df[col1], df[col2]
            label1, label2 = col1, col2

        elif (is_col1_numeric and not is_col2_numeric) or (is_col2_numeric and not is_col1_numeric):
            num_col, cat_col = (col1, col2) if is_col1_numeric else (col2, col1)
            box_df = df[[cat_col, num_col]]
            unique_groups = box_df[cat_col].unique()
            if len(unique_groups) != 2:
                raise ValueError("Categorical column must have exactly two groups.")

            group1 = box_df[box_df[cat_col] == unique_groups[0]][num_col]
            group2 = box_df[box_df[cat_col] == unique_groups[1]][num_col]
            series1, series2 = group1, group2
            label1, label2 = str(unique_groups[0]), str(unique_groups[1])

        else:
            raise ValueError("At least one column must be numeric for t-test.")

        # Normality check
        def check_normality(s):
            if len(s) < 30:
                stat, p = shapiro(s)
                return p >= 0.05, f"Shapiro-Wilk p = {p:.4f} → {'normal' if p >= 0.05 else 'not normal'} (n = {len(s)})"
            else:
                return True, f"Sample size ≥ 30 (n = {len(s)}) → assumed normal by CLT"

        normal1, note1 = check_normality(series1)
        normal2, note2 = check_normality(series2)

        use_mannwhitney = not (normal1 and normal2)

        if use_mannwhitney:
            test_type = "Mann–Whitney U test"
            stat, p_value = mannwhitneyu(series1, series2, alternative="two-sided")
            df_used = "N/A"
            levene_p = None
            equal_var = None
        else:
            test_type = "Independent t-test"
            levene_stat, levene_p = levene(series1, series2)
            equal_var = levene_p > 0.05
            stat, p_value = ttest_ind(series1, series2, equal_var=equal_var)
            df_used = len(series1) + len(series2) - 2 if equal_var else (
                (series1.var(ddof=1)/len(series1) + series2.var(ddof=1)/len(series2))**2 /
                (((series1.var(ddof=1)/len(series1))**2) / (len(series1)-1) +
                 ((series2.var(ddof=1)/len(series2))**2) / (len(series2)-1))
            )

        # Directional interpretation
        center1 = np.median(series1) if use_mannwhitney else np.mean(series1)
        center2 = np.median(series2) if use_mannwhitney else np.mean(series2)
        if p_value < 0.05:
            if center1 > center2:
                direction = f"{label1} is higher than {label2}."
            elif center2 > center1:
                direction = f"{label2} is higher than {label1}."
            else:
                direction = "No clear directional difference."
        else:
            direction = "No significant directional difference."

        # Interpretation string
        df_str = f"{round(df_used, 2)}" if isinstance(df_used, (int, float, np.number)) else "N/A"
        levene_note = (
            f"Levene's test p = {levene_p:.4f} → "
            f"{'Equal variance assumed' if equal_var else 'Equal variance not assumed'}"
            if levene_p is not None else ""
        )

        interpretation = (
            f"{test_type}:\n"
            f"Test statistic = {stat:.4f}\n"
            f"Degrees of freedom = {df_str}\n"
            f"p-value = {p_value:.4f} → "
            f"{'Statistically significant (p < 0.05)' if p_value < 0.05 else 'Not statistically significant'}\n"
            f"{direction}\n\n"
            f"{levene_note}\n\n"
            f"Normality assessment:\n"
            f"{label1}: {note1}\n"
            f"{label2}: {note2}"
        )

        # Plot
        plot_df = pd.DataFrame({
            "Group": [label1] * len(series1) + [label2] * len(series2),
            "Value": pd.concat([series1, series2], ignore_index=True)
        })
        fig = px.box(plot_df, x="Group", y="Value", title=f"{label1} vs {label2}")
        fig.update_layout(xaxis_title=None, yaxis_title="Value", template="plotly_white", boxmode="group")

        fig_dict = fig.to_plotly_json()
        plotly_data = json.loads(json.dumps(fig_dict["data"], cls=NumpyEncoder))
        plotly_layout = json.loads(json.dumps(fig_dict["layout"], cls=NumpyEncoder))

        return {
            "summary_text": interpretation,
            "test_type": test_type,
            "plotly_data": plotly_data,
            "plotly_layout": plotly_layout,
            "posthoc": None
        }


    def _anova_test(self, df: pd.DataFrame, group_col: str, value_col: str) -> dict:
        df_clean = df[[group_col, value_col]].dropna()

        # Group data
        grouped = df_clean.groupby(group_col)[value_col]
        group_names = list(grouped.groups.keys())
        group_values = [grouped.get_group(name) for name in group_names]

        # Shapiro-Wilk test for normality if n < 30
        normality_notes = []
        all_normal = True
        for name, group in zip(group_names, group_values):
            if len(group) < 30:
                _, p_shapiro = shapiro(group)
                normal = p_shapiro >= 0.05
                all_normal = all_normal and normal
                note = f"{name}: Shapiro-Wilk p = {p_shapiro:.4f} → {'normal' if normal else 'not normal'} (n = {len(group)})"
            else:
                note = f"{name}: Sample size ≥ 30 (n = {len(group)}) → assumed normal by CLT"
            normality_notes.append(note)

        # Decide which test to use
        if all_normal:
            stat, p_levene = levene(*group_values)

            if p_levene >= 0.05:
                f_stat, p_value = f_oneway(*group_values)
                method = "Standard ANOVA (equal variances assumed)"
                posthoc_type = "tukey"
            else:
                model = smf.ols(f'{value_col} ~ C({group_col})', data=df_clean).fit()
                welch_result = sm.stats.anova_lm(model, typ=2, robust='hc3')
                f_stat = welch_result["F"][0]
                p_value = welch_result["PR(>F)"][0]
                method = "Welch’s ANOVA (unequal variances)"
                posthoc_type = "gameshowell"
        else:
            f_stat, p_value = kruskal(*group_values)
            method = "Kruskal–Wallis H test (non-parametric)"
            posthoc_type = "dunn"

        # Construct boxplot
        filtered_df = pd.concat([
            pd.DataFrame({group_col: [label] * len(group), value_col: group})
            for label, group in zip(group_names, group_values)
        ])

        fig = px.box(
            filtered_df,
            x=group_col,
            y=value_col,
            title=f"{value_col} by {group_col}"
        )
        fig.update_layout(xaxis_title=group_col, yaxis_title=value_col)

        fig_dict = fig.to_plotly_json()
        plotly_data = json.loads(json.dumps(fig_dict["data"], cls=NumpyEncoder))
        plotly_layout = json.loads(json.dumps(fig_dict["layout"], cls=NumpyEncoder))

        # Construct interpretation string
        interpretation = (
            f"{method} for '{value_col}' by '{group_col}': "
            f"F = {f_stat:.4f}, p = {p_value:.4f} → "
            f"{'Significant' if p_value < 0.05 else 'Not significant'}\n\n"
            f"Normality assessment:\n" + "\n".join(normality_notes)
        )

        # Post hoc analysis
        posthoc_results = None
        if p_value < 0.05:
            try:
                group_means = df_clean.groupby(group_col)[value_col].mean().to_dict()

                def get_direction(g1, g2):
                    mean1, mean2 = group_means[g1], group_means[g2]
                    if mean1 > mean2:
                        return f"{g1} > {g2}"
                    elif mean1 < mean2:
                        return f"{g1} < {g2}"
                    else:
                        return f"{g1} = {g2}"

                if posthoc_type == "tukey":
                    tukey_result = pairwise_tukeyhsd(endog=df_clean[value_col], groups=df_clean[group_col], alpha=0.05)
                    tukey_df = pd.DataFrame(data=tukey_result._results_table.data[1:], columns=tukey_result._results_table.data[0])
                    tukey_df["Direction"] = tukey_df.apply(lambda row: get_direction(row["group1"], row["group2"]), axis=1)
                    tukey_df = tukey_df.rename(columns={
                        "group1": "Group 1",
                        "group2": "Group 2",
                        "p-adj": "Adjusted p-value"
                    })
                    posthoc_results = tukey_df[["Group 1", "Group 2", "Adjusted p-value", "Direction"]].to_string(index=False)

                elif posthoc_type == "gameshowell":
                    posthoc_df = pg.pairwise_gameshowell(dv=value_col, between=group_col, data=df_clean)
                    posthoc_df["Direction"] = posthoc_df.apply(lambda row: get_direction(row["A"], row["B"]), axis=1)
                    posthoc_df = posthoc_df.rename(columns={
                        "A": "Group 1",
                        "B": "Group 2",
                        "pval": "Adjusted p-value"
                    })
                    posthoc_results = posthoc_df[["Group 1", "Group 2", "Adjusted p-value", "Direction"]].to_string(index=False)

                elif posthoc_type == "dunn":

                    # Run Dunn's test using scikit-posthocs
                    dunn_df = sp.posthoc_dunn(
                        df_clean, val_col=value_col, group_col=group_col, p_adjust='bonferroni'
                    ).reset_index().rename(columns={'index': 'Group 1'})

                    # Melt into long format
                    posthoc_df = dunn_df.melt(id_vars=["Group 1"], var_name="Group 2", value_name="Adjusted p-value")

                    # Add direction column
                    posthoc_df["Direction"] = posthoc_df.apply(
                        lambda row: get_direction(row["Group 1"], row["Group 2"]), axis=1
                    )

                    # Final output
                    posthoc_results = posthoc_df[
                        ["Group 1", "Group 2", "Adjusted p-value", "Direction"]
                    ].to_string(index=False)

            except Exception as e:
                posthoc_results = f"Post hoc analysis failed: {e}"

        return {
            "summary_text": interpretation,
            "posthoc": posthoc_results,
            "plotly_data": plotly_data,
            "plotly_layout": plotly_layout,
            "table": df_clean.head().to_dict("records"),
            "test_type": "anova"
        }
