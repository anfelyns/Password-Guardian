# -*- coding: utf-8 -*-
# database/engine.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

# --- DB config (no .env, per your preference) ---
DB_USER = "root"
DB_PASS = "inessouai2005_"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "password_guardian"

#  Use PyMySQL 
DB_URL = (
    f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASS)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    f"?charset=utf8mb4"
)

engine = create_engine(
    DB_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=1800,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)
