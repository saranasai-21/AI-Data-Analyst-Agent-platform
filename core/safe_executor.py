import builtins
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go


class SafeExecutor:

    @staticmethod
    def _get_safe_builtins():
        # Curated safe builtins to prevent NameError for len, range, sum, str, etc.
        # We explicitly exclude dangerous built-ins to maintain a safe environment.
        forbidden = {'open', 'eval', 'exec', 'compile', '__import__', 'globals', 'locals', 'input', 'exit', 'quit'}
        return {k: v for k, v in builtins.__dict__.items() if k not in forbidden}

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
                "__builtins__": SafeExecutor._get_safe_builtins()
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
                "__builtins__": SafeExecutor._get_safe_builtins()
            },
            scope
        )

        return scope.get(
            "fig",
            None
        )