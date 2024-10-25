import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json
import json
import sys
from datetime import datetime


# Load environment variables from .env file
load_dotenv()

# Determine if we are running in test or production
environment = os.getenv('ENVIRONMENT', 'production')

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )

# Function to create tables if they don't exist
def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    tables = ['search_inputs', 'flight_prices', 'parsed_offers']
    try:
        for table in tables:
            full_table_name = f"{table}_{environment}"
            if table == 'search_inputs':
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {full_table_name} (
                        id SERIAL PRIMARY KEY,
                        data JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            else:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {full_table_name} (
                        id SERIAL PRIMARY KEY,
                        search_inputs_id INTEGER,
                        data JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (search_inputs_id) REFERENCES search_inputs_{environment}(id)
                    )
                """)
        conn.commit()
        print("Tables created successfully", file=sys.stderr)
    except Exception as e:
        print(f"An error occurred while creating tables: {e}", file=sys.stderr)
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def get_past_searches(limit=10):
    conn = get_db_connection()
    cur = conn.cursor()
    table_name = f"searches_{environment}"
    cur.execute(f"""
        SELECT id, search_inputs, search_time 
        FROM {table_name} 
        ORDER BY search_time DESC 
        LIMIT %s
    """, (limit,))
    searches = cur.fetchall()
    cur.close()
    conn.close()
    return searches

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

def insert_data(data, table_name, search_inputs_id=None):
    conn = get_db_connection()
    cur = conn.cursor()
    full_table_name = f"{table_name}_{environment}"
    try:
        # Use the custom encoder to handle datetime objects
        json_data = json.dumps(data, cls=DateTimeEncoder)
        if table_name == 'search_inputs' or search_inputs_id is None:
            cur.execute(f"""
                INSERT INTO {full_table_name} (data)
                VALUES (%s)
                RETURNING id
            """, (json_data,))
        else:
            cur.execute(f"""
                INSERT INTO {full_table_name} (search_inputs_id, data)
                VALUES (%s, %s)
                RETURNING id
            """, (search_inputs_id, json_data))
        record_id = cur.fetchone()[0]
        conn.commit()
        print(f"Data successfully inserted into {full_table_name} with ID: {record_id}", file=sys.stderr)
        return record_id
    except Exception as e:
        print(f"An error occurred while inserting data into {full_table_name}: {e}", file=sys.stderr)
        conn.rollback()
        return None
    finally:
        cur.close()
        conn.close()
