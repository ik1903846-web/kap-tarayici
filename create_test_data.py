import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "kap_data.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY, code TEXT, title TEXT, updated_at TEXT)""")

c.execute("""CREATE TABLE IF NOT EXISTS financials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT, period TEXT, year INTEGER, quarter INTEGER,
    table_type TEXT, label TEXT, value REAL, currency TEXT DEFAULT 'TRY',
    updated_at TEXT, UNIQUE(company_id, period, table_type, label))""")

companies = [
    ("thyao", "THYAO", "Türk Hava Yolları"),
    ("garan", "GARAN", "Garanti Bankası"),
    ("akbnk", "AKBNK", "Akbank"),
    ("eregl", "EREGL", "Ereğli Demir Çelik"),
    ("bimas", "BIMAS", "BİM Mağazalar"),
]

for cid, code, title in companies:
    c.execute("INSERT OR REPLACE INTO companies (id,code,title,updated_at) VALUES (?,?,?,datetime('now'))",
              (cid, code, title))

data = [
    ("thyao", 2024, "Gelir Tablosu", "Net Satışlar", 450000000),
    ("thyao", 2023, "Gelir Tablosu", "Net Satışlar", 380000000),
    ("thyao", 2022, "Gelir Tablosu", "Net Satışlar", 290000000),
    ("thyao", 2021, "Gelir Tablosu", "Net Satışlar", 180000000),
    ("thyao", 2024, "Gelir Tablosu", "Net Kar", 85000000),
    ("thyao", 2023, "Gelir Tablosu", "Net Kar", 72000000),
    ("thyao", 2022, "Gelir Tablosu", "Net Kar", 48000000),
    ("thyao", 2021, "Gelir Tablosu", "Net Kar", 12000000),
    ("garan", 2024, "Gelir Tablosu", "Net Faiz Geliri", 120000000),
    ("garan", 2023, "Gelir Tablosu", "Net Faiz Geliri", 98000000),
    ("garan", 2022, "Gelir Tablosu", "Net Faiz Geliri", 75000000),
    ("garan", 2021, "Gelir Tablosu", "Net Faiz Geliri", 52000000),
]

for cid, year, ttype, label, val in data:
    c.execute("""INSERT OR REPLACE INTO financials
        (company_id,period,year,quarter,table_type,label,value,updated_at)
        VALUES (?,?,?,4,?,?,?,datetime('now'))""",
        (cid, str(year), year, ttype, label, val))

conn.commit()
conn.close()
print("Test verisi eklendi!")
