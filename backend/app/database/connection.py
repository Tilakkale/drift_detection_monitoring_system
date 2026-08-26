import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

load_dotenv()

# Primary MySQL config (can be overridden by .env)
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "drift_monitoring")

MYSQL_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Try MySQL first, fall back to a local SQLite file if MySQL is unavailable.
engine = None
try:
    engine = create_engine(MYSQL_URL, pool_pre_ping=True)
    # Test a quick connection
    conn = engine.connect()
    conn.close()
    print(f"Using MySQL database at {DB_HOST}:{DB_PORT}/{DB_NAME}")
except Exception as e:
    sqlite_url = "sqlite:///./backend.db"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    print("Warning: falling back to SQLite (backend.db). Reason:", e)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()