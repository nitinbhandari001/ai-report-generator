import asyncio

import pandas as pd

from src.exceptions import DatabaseError, IngestionError


def _read_sql(query: str, database_url: str) -> pd.DataFrame:
    try:
        import sqlalchemy

        engine = sqlalchemy.create_engine(database_url)
        with engine.connect() as conn:
            return pd.read_sql(query, conn)
    except Exception as exc:
        raise DatabaseError(str(exc)) from exc


async def load_from_query(query: str, database_url: str) -> pd.DataFrame:
    if not query.strip().upper().startswith("SELECT"):
        raise IngestionError("Query must start with SELECT")
    return await asyncio.to_thread(_read_sql, query, database_url)
