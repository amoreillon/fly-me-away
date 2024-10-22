import streamlit as st
import psycopg2
from psycopg2.extras import Json
import json
import sys


# Determine if we are running in test or production
environment = st.secrets.get("environment", "production")  # Defaults to production if not set

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        host=st.secrets["neon_db"]["host"],
        database=st.secrets["neon_db"]["database"],
        user=st.secrets["neon_db"]["user"],
        password=st.secrets["neon_db"]["password"]
    )

# Function to create tables if they don't exist
def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    tables = ['search_inputs', 'flight_prices', 'parsed_offers']
    try:
        for table in tables:
            full_table_name = f"{table}_{environment}"
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {full_table_name} (
                    id SERIAL PRIMARY KEY,
                    data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def insert_data(data, table_name):
    conn = get_db_connection()
    cur = conn.cursor()
    full_table_name = f"{table_name}_{environment}"
    try:
        cur.execute(f"""
            INSERT INTO {full_table_name} (data)
            VALUES (%s)
            RETURNING id
        """, (Json(data),))
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
