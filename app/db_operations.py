import streamlit as st
import psycopg2
from psycopg2.extras import Json
import json


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
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        table_name = f"searches_{environment}"
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                search_inputs JSONB,
                flight_prices JSONB,
                all_parsed_offers JSONB,
                search_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except Exception as e:
        st.error(f"An error occurred while creating tables: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# Function to insert search data
def insert_search_data(search_inputs, flight_prices, all_parsed_offers):
    conn = get_db_connection()
    cur = conn.cursor()
    table_name = f"searches_{environment}"
    cur.execute(f"""
        INSERT INTO {table_name} (search_inputs, flight_prices, all_parsed_offers)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (Json(search_inputs), Json(flight_prices), Json(all_parsed_offers)))
    search_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return search_id

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