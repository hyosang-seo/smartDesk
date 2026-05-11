import os
import certifi
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 4000))
DB_NAME = os.getenv("DB_NAME", "seat_db")

print(f"Connecting to {DB_HOST} to check/create database '{DB_NAME}'...")

try:
    # 데이터베이스 지정 없이 연결
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        ssl={'ca': certifi.where()}
    )
    with conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"Successfully created or verified database '{DB_NAME}'.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
