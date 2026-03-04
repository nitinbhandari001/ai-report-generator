import asyncio

import pandas as pd
import structlog

from src.exceptions import DatabaseError, IngestionError

log = structlog.get_logger(__name__)


class DatabaseService:
    def __init__(self, database_url: str) -> None:
        self._url = database_url

    @property
    def is_configured(self) -> bool:
        return bool(self._url)

    def _run_query(self, query: str) -> pd.DataFrame:
        try:
            import sqlalchemy
            engine = sqlalchemy.create_engine(self._url)
            with engine.connect() as conn:
                return pd.read_sql(query, conn)
        except Exception as exc:
            raise DatabaseError(str(exc)) from exc

    async def execute_query(self, query: str) -> pd.DataFrame:
        if not self.is_configured:
            return pd.DataFrame()
        if not query.strip().upper().startswith("SELECT"):
            raise IngestionError("Query must start with SELECT")
        return await asyncio.to_thread(self._run_query, query)
