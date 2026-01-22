import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import List, Dict, Any, Optional


class RelationalMemory:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        # Ensure we have a valid connection string or parameters
        if not self.db_url:
            # Fallback to environment variables if DATABASE_URL is not set
            user = os.getenv("DB_USER", "postgres")
            password = os.getenv("DB_PASSWORD", "postgres")
            host = os.getenv("DB_HOST", "postgres")
            port = os.getenv("DB_PORT", "5432")
            dbname = os.getenv("DB_NAME", "fraud_forge")
            self.db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

    def get_connection(self):
        return psycopg2.connect(self.db_url)

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if cur.description:
                    return cur.fetchall()
                conn.commit()
                return []
        finally:
            conn.close()

    def execute_batch(self, query: str, params_list: List[tuple]):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, query, params_list)
            conn.commit()
        finally:
            conn.close()
