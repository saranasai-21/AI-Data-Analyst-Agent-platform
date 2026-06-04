import pandas as pd

from sqlalchemy import create_engine


class DataLoader:

    @staticmethod
    def load_file(uploaded_file):

        name = uploaded_file.name.lower()

        if name.endswith(".csv"):

            return pd.read_csv(
                uploaded_file
            )

        elif name.endswith(".xlsx") or name.endswith(".xls"):

            return pd.read_excel(
                uploaded_file
            )

        elif name.endswith(".json"):

            return pd.read_json(
                uploaded_file
            )

        raise ValueError(
            "Unsupported format"
        )

    @staticmethod
    def load_sqlite(
        db_path,
        query
    ):

        engine = create_engine(
            f"sqlite:///{db_path}"
        )

        return pd.read_sql(
            query,
            engine
        )

    @staticmethod
    def load_mysql(
        host,
        port,
        username,
        password,
        database,
        query
    ):

        engine = create_engine(

            f"mysql+pymysql://"
            f"{username}:{password}"
            f"@{host}:{port}/{database}"

        )

        return pd.read_sql(
            query,
            engine
        )

    @staticmethod
    def load_postgresql(
        host,
        port,
        username,
        password,
        database,
        query
    ):

        engine = create_engine(

            f"postgresql+psycopg2://"
            f"{username}:{password}"
            f"@{host}:{port}/{database}"

        )

        return pd.read_sql(
            query,
            engine
        )
