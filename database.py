import os

import psycopg

from dotenv import load_dotenv

load_dotenv()

class Database:

    def __init__(self):

        self.connection = None

        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:

            raise RuntimeError(
                "DATABASE_URL environment variable not found."
            )

        self.connection = psycopg.connect(
            database_url
        )