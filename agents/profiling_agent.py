import pandas as pd


class ProfilingAgent:

    def run(self, df):

        profile = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "duplicates": int(df.duplicated().sum()),
            "missing_values": (
                df.isnull()
                .sum()
                .sort_values(ascending=False)
                .to_dict()
            ),
            "data_types": (
                df.dtypes.astype(str).to_dict()
            ),
            "column_names": list(df.columns)
        }

        numeric_cols = list(
            df.select_dtypes(
                include="number"
            ).columns
        )

        if numeric_cols:
            profile["statistics"] = (
                df[numeric_cols]
                .describe()
                .to_dict()
            )
        else:
            profile["statistics"] = {}

        return profile