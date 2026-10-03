import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

conn_str = "postgresql://postgres:lightking@localhost:5432/postgres"

def init_db():
    try:
        # Connect to default postgres database to create a new one
        conn = psycopg2.connect(conn_str)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if pipeline_db exists
        cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'pipeline_db'")
        exists = cur.fetchone()
        if not exists:
            print("Creating pipeline_db...")
            cur.execute("CREATE DATABASE pipeline_db")
        else:
            print("pipeline_db already exists.")
            
        cur.close()
        conn.close()
        
        # Connect to the new pipeline_db to enable PostGIS
        conn2 = psycopg2.connect("postgresql://postgres:lightking@localhost:5432/pipeline_db")
        conn2.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur2 = conn2.cursor()
        print("Enabling PostGIS extension...")
        cur2.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        cur2.close()
        conn2.close()
        print("Database initialized successfully with PostGIS!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    init_db()
