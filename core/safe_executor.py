import pandas as pd

import plotly.express as px
import plotly.graph_objects as go


class SafeExecutor:

    @staticmethod
    def execute_pandas(
        code,
        df
    ):

        scope = {

            "df": df,

            "pd": pd

        }

        exec(
            code,
            {
                "__builtins__": {}
            },
            scope
        )

        return scope.get(
            "result",
            None
        )

    @staticmethod
    def execute_plotly(
        code,
        df
    ):

        scope = {

            "df": df,

            "pd": pd,

            "px": px,

            "go": go

        }

        exec(
            code,
            {
                "__builtins__": {}
            },
            scope
        )

        return scope.get(
            "fig",
            None
        )