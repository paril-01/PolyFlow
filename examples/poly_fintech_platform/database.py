"""
PolyFinTech Enterprise OS — SQLite Database & Persistence Layer.

Provides relational storage for users, multi-currency accounts, virtual cards,
SWIFT wire transfers, loan applications, and audit records.
"""

import os
import sqlite3
import json
import time
import hashlib
from pathlib import Path

DB_PATH = Path(__file__).parent / "fintech.db"

def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        company_name TEXT NOT NULL,
        role TEXT NOT NULL,
        kyc_status TEXT NOT NULL DEFAULT 'VERIFIED',
        created_at REAL NOT NULL
    )
    """)

    # 2. Accounts Table (Multi-currency Treasury)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        account_number TEXT UNIQUE NOT NULL,
        currency TEXT NOT NULL,
        balance REAL NOT NULL,
        account_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    """)

    # 3. Virtual Cards Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS virtual_cards (
        card_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        card_number TEXT UNIQUE NOT NULL,
        cardholder_name TEXT NOT NULL,
        expiry TEXT NOT NULL,
        cvv TEXT NOT NULL,
        spend_limit REAL NOT NULL,
        spent_amount REAL NOT NULL DEFAULT 0.0,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        created_at REAL NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    """)

    # 4. Transactions & Wires Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        tx_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        account_id TEXT NOT NULL,
        tx_type TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        recipient TEXT NOT NULL,
        description TEXT NOT NULL,
        risk_score REAL NOT NULL DEFAULT 0.05,
        status TEXT NOT NULL DEFAULT 'COMPLETED',
        timestamp REAL NOT NULL,
        merkle_root TEXT
    )
    """)

    # Seed Data if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        now = time.time()

        # Seed User
        pass_hash = hashlib.sha256("Password123!".encode()).hexdigest()
        cursor.execute("""
        INSERT INTO users (user_id, username, password_hash, full_name, company_name, role, kyc_status, created_at)
        VALUES ('usr_corp_101', 'executive@enterprise.com', ?, 'Alexander Vance', 'PolyFinTech Global Corp', 'cfo', 'VERIFIED', ?)
        """, (pass_hash, now))

        # Seed Multi-Currency Accounts
        cursor.execute("INSERT INTO accounts VALUES ('acc_usd_01', 'usr_corp_101', 'US89-3301-4491-001', 'USD', 2450000.00, 'Operating', 'ACTIVE')")
        cursor.execute("INSERT INTO accounts VALUES ('acc_eur_02', 'usr_corp_101', 'EU42-9981-2200-002', 'EUR', 1850000.00, 'Treasury', 'ACTIVE')")
        cursor.execute("INSERT INTO accounts VALUES ('acc_gbp_03', 'usr_corp_101', 'GB11-5544-7788-003', 'GBP', 920000.00, 'Payroll', 'ACTIVE')")
        cursor.execute("INSERT INTO accounts VALUES ('acc_btc_04', 'usr_corp_101', 'bc1q-polyflow-node-004', 'BTC', 42.50, 'Digital Assets', 'ACTIVE')")

        # Seed Virtual Corporate Cards
        cursor.execute("INSERT INTO virtual_cards VALUES ('card_vc_01', 'usr_corp_101', '4532 •••• •••• 8891', 'Alexander Vance', '08/29', '741', 50000.00, 12450.00, 'ACTIVE', ?)", (now,))
        cursor.execute("INSERT INTO virtual_cards VALUES ('card_vc_02', 'usr_corp_101', '5412 •••• •••• 3342', 'Engineering Cloud Team', '11/28', '298', 25000.00, 4800.00, 'ACTIVE', ?)", (now,))
        cursor.execute("INSERT INTO virtual_cards VALUES ('card_vc_03', 'usr_corp_101', '3782 •••• •••• 9912', 'Executive Travel', '04/30', '104', 100000.00, 31200.00, 'FROZEN', ?)", (now,))

        # Seed Recent Transactions
        cursor.execute("INSERT INTO transactions VALUES ('tx_init_101', 'usr_corp_101', 'acc_usd_01', 'WIRE_TRANSFER', 150000.00, 'USD', 'Goldman Sachs Institutional', 'Q3 Treasury Rebalance', 0.02, 'COMPLETED', ?, 'hash_initial_seed_1')", (now - 86400,))
        cursor.execute("INSERT INTO transactions VALUES ('tx_init_102', 'usr_corp_101', 'acc_eur_02', 'SWIFT_ISO20022', 75000.00, 'EUR', 'BNP Paribas France', 'EU Cloud Infrastructure Invoice', 0.05, 'COMPLETED', ?, 'hash_initial_seed_2')", (now - 43200,))

    conn.commit()
    conn.close()

init_db()
