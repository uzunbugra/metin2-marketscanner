import os
import sqlite3
import asyncio
import random
import sys
import json
import argparse
from datetime import datetime
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "metin2.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "database", "schema.sql")
URL = "https://metin2alerts.com/store"
HISTORY_EXPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "exports")

def init_db():
    """Initialize the database with the schema."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(HISTORY_EXPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = f.read()
        cursor.executescript(schema)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def parse_price(price_str):
    """Clean and convert price strings like '1 w', '50 m', '10.000'."""
    if not price_str: return 0
    clean_str = price_str.lower().replace('.', '').strip()
    
    multiplier = 1
    if 'w' in clean_str:
        multiplier = 100000000
        clean_str = clean_str.replace('w', '')
    elif 'm' in clean_str:
        multiplier = 1000000
        clean_str = clean_str.replace('m', '')
    elif 'k' in clean_str:
        multiplier = 1000
        clean_str = clean_str.replace('k', '')
        
    try:
        return int(float(clean_str) * multiplier)
    except ValueError:
        return 0

async def analyze_market(search_query):
    """Calculates market stats and saves to price_history."""
    print(f"Analyzing market for '{search_query}'...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # We analyze listings for the items matching the search query
        # Calculate unit_price in SQL: total_price_yang / quantity
        # Filter where quantity > 0
        
        query = """
            SELECT 
                i.name,
                COUNT(*) as total_listings,
                MIN(l.total_price_yang / l.quantity) as min_unit_price,
                AVG(l.total_price_yang / l.quantity) as avg_unit_price
            FROM listings l
            JOIN items i ON l.item_id = i.id
            WHERE i.name LIKE ? AND l.quantity > 0
            GROUP BY i.name
        """
        
        cursor.execute(query, (f"%{search_query}%",))
        results = cursor.fetchall()
        
        timestamp = datetime.now()
        
        for row in results:
            item_name, total, min_price, avg_price = row
            
            # Save to history
            cursor.execute("""
                INSERT INTO price_history (item_name, avg_unit_price, min_unit_price, total_listings, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (item_name, int(avg_price), int(min_price), total, timestamp))
            
            print(f"Recorded history for {item_name}: Avg {int(avg_price):,} Yang, Min {int(min_price):,} Yang, Count {total}")
            
            # Export JSON for this item
            export_history_to_json(item_name, cursor)
            
        conn.commit()
        
    except Exception as e:
        print(f"Error in market analysis: {e}")
    finally:
        conn.close()

def export_history_to_json(item_name, cursor):
    """Exports price history for an item to JSON for Chart.js."""
    try:
        cursor.execute("""
            SELECT timestamp, avg_unit_price, min_unit_price, total_listings 
            FROM price_history 
            WHERE item_name = ? 
            ORDER BY timestamp ASC
        """, (item_name,))
        
        rows = cursor.fetchall()
        data = [
            {
                "timestamp": row[0],
                "avg_unit_price": row[1],
                "min_unit_price": row[2],
                "total_listings": row[3]
            } 
            for row in rows
        ]
        
        # Clean filename
        safe_name = "".join([c for c in item_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
        filepath = os.path.join(HISTORY_EXPORT_DIR, f"history_{safe_name}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"Exported history to {filepath}")
        
    except Exception as e:
        print(f"Error exporting JSON for {item_name}: {e}")

async def scrape_store(search_query=None):
    if not search_query:
        search_query = os.environ.get("SEARCH_QUERY")
        
    print(f"Starting scrape for '{search_query}' at {URL}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(URL, timeout=60000)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # Select Server (Marmara)
            try:
                selects = await page.query_selector_all("select")
                if selects:
                    await page.select_option("select", value="409")
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(2)
                else:
                    marmara_link = page.get_by_text("Marmara")
                    if await marmara_link.count() > 0:
                        await marmara_link.first.click(force=True)
                        await page.wait_for_load_state("networkidle")
                        await asyncio.sleep(2)
            except Exception as e:
                print(f"Error selecting Marmara: {e}")

            # Search
            if search_query:
                try:
                    search_input = page.locator("#item-search-input")
                    if await search_input.is_visible():
                        await search_input.click()
                        await search_input.fill("")
                        await asyncio.sleep(0.5)
                        await search_input.type(search_query, delay=100)
                        await asyncio.sleep(0.5)
                        await search_input.press("Enter")
                        await page.wait_for_load_state("networkidle")
                        await asyncio.sleep(3)
                except Exception as e:
                    print(f"Error searching: {e}")

            # Pagination Loop
            all_listings = []
            page_num = 1
            
            while True:
                print(f"--- Page {page_num} ---")
                try:
                    await page.wait_for_selector("tbody tr", timeout=10000)
                except:
                    print("No rows found.")
                    if page_num == 1: break
                
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                rows = soup.select("tbody tr")
                
                print(f"Rows: {len(rows)}")
                
                for row in rows:
                    try:
                        cols = row.find_all('td')
                        if len(cols) < 5: continue
                        
                        info_col = cols[1]
                        name_div = info_col.find('div', class_=lambda x: x and 'font-medium' in x)
                        item_name = ""
                        special_bonuses = []
                        
                        if name_div:
                            name_spans = name_div.find_all('span')
                            special_bonuses = [s.get_text(strip=True) for s in name_spans]
                            for s in name_spans: s.extract()
                            item_name = name_div.get_text(strip=True)
                        else:
                            item_name = info_col.get_text(strip=True)
                        
                        bonus_div = info_col.find('div', class_=lambda x: x and 'text-xs' in x and 'text-gray-400' in x)
                        bonuses = []
                        if bonus_div:
                            bonuses = [s.get_text(strip=True) for s in bonus_div.find_all('span')]
                        bonuses.extend(special_bonuses)
                        
                        quantity = parse_price(cols[2].get_text(strip=True)) or 1
                        yang = parse_price(cols[3].get_text(strip=True))
                        won = parse_price(cols[4].get_text(strip=True))
                        seller = cols[5].get_text(strip=True) if len(cols) > 5 else "Unknown"
                        
                        total_yang = (won * 100_000_000) + yang
                        unit_price = total_yang / quantity
                        
                        all_listings.append({
                            "item_name": item_name,
                            "seller": seller,
                            "quantity": quantity,
                            "price_won": won,
                            "price_yang": yang,
                            "total_yang": total_yang,
                            "unit_price": unit_price,
                            "bonuses": bonuses
                        })
                    except Exception:
                        continue
                
                # Next Page
                next_button = None
                candidates = page.locator("button:has-text('>')")
                if await candidates.count() > 0: next_button = candidates.first
                elif await page.locator("button:has-text('Sonraki')").count() > 0: next_button = page.locator("button:has-text('Sonraki')").first
                elif await page.locator("button:has-text('Next')").count() > 0: next_button = page.locator("button:has-text('Next')").first
                
                if next_button and await next_button.is_visible() and not await next_button.is_disabled():
                    await next_button.click()
                    await page.wait_for_load_state("networkidle")
                    await asyncio.sleep(random.uniform(1, 3))
                    page_num += 1
                else:
                    break
            
            # Deduplicate & Sort
            unique_listings = []
            seen = set()
            for item in all_listings:
                sig = (item['item_name'], item['seller'], item['total_yang'], item['quantity'])
                if sig not in seen:
                    seen.add(sig)
                    unique_listings.append(item)
            unique_listings.sort(key=lambda x: x['unit_price'])
            
            await save_to_db(unique_listings, search_query)
            
            # ANALYZE AFTER SAVE
            if search_query:
                await analyze_market(search_query)
            else:
                # If no specific query, we might want to analyze all updated items
                # For now, let's skip or analyze distinct items found
                found_names = set(i['item_name'] for i in unique_listings)
                for name in found_names:
                    await analyze_market(name)
            
        except Exception as e:
            print(f"Scrape error: {e}")
        finally:
            await browser.close()

async def save_to_db(listings, search_query):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    server_id = 409 # Marmara hardcoded for now or fetch
    cursor.execute("INSERT OR IGNORE INTO servers (name) VALUES (?)", ("Marmara",))
    
    if search_query:
         cursor.execute("DELETE FROM listings WHERE item_id IN (SELECT id FROM items WHERE name LIKE ?)", (f"%{search_query}%",))
         cursor.execute("DELETE FROM listing_bonuses WHERE listing_id NOT IN (SELECT id FROM listings)")
    
    count = 0
    for item in listings:
        cursor.execute("INSERT OR IGNORE INTO items (name, category) VALUES (?, ?)", (item['item_name'], "General"))
        item_id = cursor.execute("SELECT id FROM items WHERE name=?", (item['item_name'],)).fetchone()[0]
        
        cursor.execute("""
            INSERT INTO listings (server_id, item_id, seller_name, quantity, price_won, price_yang, total_price_yang)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (server_id, item_id, item['seller'], item['quantity'], item['price_won'], item['price_yang'], item['total_yang']))
        
        listing_id = cursor.lastrowid
        for bonus in item['bonuses']:
            if bonus:
                cursor.execute("INSERT INTO listing_bonuses (listing_id, bonus_name, bonus_value) VALUES (?, ?, ?)", (listing_id, bonus, ""))
        count += 1
            
    conn.commit()
    conn.close()
    print(f"Saved {count} listings.")

async def run_bot(interval_minutes=20):
    """Infinite loop for the bot."""
    print(f"Starting Market Bot (Interval: {interval_minutes} mins)")
    search_query = os.environ.get("SEARCH_QUERY", "Dolunay") # Default item to watch
    
    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Bot execution started...")
        await scrape_store(search_query)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sleeping for {interval_minutes} minutes...")
        await asyncio.sleep(interval_minutes * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Metin2 Market Scraper & Bot")
    parser.add_argument("--bot", action="store_true", help="Run in continuous bot mode")
    parser.add_argument("--query", type=str, help="Search query (override env var)")
    parser.add_argument("--interval", type=int, default=20, help="Bot interval in minutes")
    
    args = parser.parse_args()
    
    # Initialize DB first
    init_db()
    
    if args.query:
        os.environ["SEARCH_QUERY"] = args.query
        
    if args.bot:
        try:
            asyncio.run(run_bot(args.interval))
        except KeyboardInterrupt:
            print("Bot stopped by user.")
    else:
        asyncio.run(scrape_store())