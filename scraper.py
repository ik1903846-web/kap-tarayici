"""
KAP Finansal Veri Tarayıcısı
"""

import requests
import json
import sqlite3
import time
import os
from datetime import datetime
from bs4 import BeautifulSoup

DB_PATH = "kap_data.db"
BASE_URL = "https://kap.org.tr"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Referer": "https://kap.org.tr/tr/",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

CURRENT_YEAR = datetime.now().year
TARGET_YEARS = list(range(CURRENT_YEAR - 3, CURRENT_YEAR + 1))

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY, code TEXT, title TEXT, updated_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS financials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT, period TEXT, year INTEGER, quarter INTEGER,
            table_type TEXT, label TEXT, value REAL, currency TEXT DEFAULT 'TRY',
            updated_at TEXT,
            UNIQUE(company_id, period, table_type, label)
        )
    """)
    conn.commit()
    conn.close()

def save_company(company_id, code, title):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO companies (id, code, title, updated_at) VALUES (?,?,?,?)",
        (company_id, code, title, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def save_financials(company_id, period, year, quarter, table_type, rows, currency="TRY"):
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().isoformat()
    for label, value in rows:
        conn.execute("""
            INSERT OR REPLACE INTO financials
            (company_id, period, year, quarter, table_type, label, value, currency, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (company_id, period, year, quarter, table_type, label, value, currency, now))
    conn.commit()
    conn.close()

def get_company_list():
    print("Şirket listesi çekiliyor...")
    try:
        url = f"{BASE_URL}/tr/api/memberCompanyInfoList/BIST"
        r = SESSION.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        companies = []
        for item in data:
            cid   = item.get("memberOid") or item.get("companyId") or item.get("oid")
            code  = item.get("ticker") or item.get("stock") or item.get("code") or ""
            title = item.get("title") or item.get("companyName") or item.get("name") or ""
            if cid and title:
                companies.append({"id": cid, "code": code, "title": title})
        if companies:
            print(f"  → {len(companies)} şirket bulundu")
            return companies
    except Exception as e:
        print(f"  ! Hata: {e}")
    return []

def get_financial_data(company_id):
    url = f"{BASE_URL}/tr/sirket-finansal-bilgileri/{company_id}"
    try:
        r = SESSION.get(url, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        tables = {}
        for idx, table in enumerate(soup.find_all("table")):
            headers, rows = [], []
            for i, tr in enumerate(table.find_all("tr")):
                cells = [td.get_text(strip=True) for td in tr.find_all(["th","td"])]
                if i == 0: headers = cells
                elif any(c for c in cells): rows.append(cells)
            if headers and rows:
                tables[f"tablo_{idx+1}"] = {"basliklar": headers, "satirlar": rows}
        return tables if tables else None
    except Exception as e:
        print(f"    ! Hata: {e}")
        return None

def run_scraper(limit=None):
    print(f"\n{'='*50}")
    print("  KAP Finansal Veri Tarayıcısı")
    print(f"  Hedef yıllar: {TARGET_YEARS}")
    print(f"{'='*50}\n")

    init_db()
    companies = get_company_list()
    if limit:
        companies = companies[:limit]

    total = len(companies)
    for i, company in enumerate(companies, 1):
        cid, code, title = company["id"], company["code"], company["title"]
        print(f"[{i:4d}/{total}] {code:6s} | {title[:35]}", end=" ")
        save_company(cid, code, title)
        data = get_financial_data(cid)
        if data:
            print("✓")
            for tname, tdata in data.items():
                rows = [(f"{tname}/{r[0]}", float(r[1].replace(',','').replace('.','')) if len(r)>1 and r[1].replace(',','').replace('.','').lstrip('-').isdigit() else 0)
                        for r in tdata.get("satirlar", []) if r]
                if rows:
                    save_financials(cid, str(CURRENT_YEAR), CURRENT_YEAR, 4, tname, rows)
        else:
            print("✗")
        time.sleep(0.5)

    print(f"\nTamamlandı! {total} şirket işlendi.")

if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_scraper(limit=limit)
