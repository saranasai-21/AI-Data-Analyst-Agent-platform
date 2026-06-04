import numpy as np
import pandas as pd


class DataQualityAgent:

    def run(self, df):

        report = {}

        report["duplicates"] = int(
            df.duplicated().sum()
        )

        report["missing_values"] = (
            df.isnull()
            .sum()
            .sort_values(
                ascending=False
            )
            .to_dict()
        )

        report["data_types"] = (
            df.dtypes
            .astype(str)
            .to_dict()
        )

        outliers = {}

        numeric_cols = list(
            df.select_dtypes(
                include=np.number
            ).columns
        )

        for col in numeric_cols:

            series = df[col].dropna()

            if len(series) == 0:
                outliers[col] = 0
                continue

            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)

            iqr = q3 - q1

            lower = q1 - (1.5 * iqr)
            upper = q3 + (1.5 * iqr)

            count = (
                (
                    (series < lower)
                    |
                    (series > upper)
                )
            ).sum()

            outliers[col] = int(count)

        report["outliers"] = outliers

        high_cardinality = {}

        categorical_cols = list(
            df.select_dtypes(
                exclude=np.number
            ).columns
        )

        for col in categorical_cols:

            unique_count = int(
                df[col].nunique()
            )

            if unique_count > 50:
                high_cardinality[col] = unique_count

        report["high_cardinality"] = (
            high_cardinality
        )

        constant_columns = []

        for col in df.columns:

            if df[col].nunique() <= 1:
                constant_columns.append(col)

        report["constant_columns"] = (
            constant_columns
        )

        report["total_rows"] = int(
            df.shape[0]
        )

        report["total_columns"] = int(
            df.shape[1]
        )

        return report