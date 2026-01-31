import os
import sqlite3
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "metin2.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "database", "schema.sql")
# Targeting the store page. 
# Observation: The site likely uses query params or local storage for server selection.
# We will try to interact with the UI to select 'Marmara' if not selected.
URL = "https://metin2alerts.com/store"

def init_db():
    """Initialize the database with the schema."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
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
        multiplier = 100000000 # 1 Won = 100m Yang approx? Or is it stored separately?
        # usually Won is separate column. If single string:
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

def scrape_store():
    print(f"Starting scrape of {URL}...")
    
    with sync_playwright() as p:
        # Launch browser (headless=False can be useful for debugging)
        browser = p.chromium.launch(headless=True) # Set to False to see what's happening
        page = browser.new_page()
        
        # Go to URL
        page.goto(URL)
        print(f"Page loaded: {page.title()}. Waiting for network idle...")
        page.wait_for_load_state("networkidle")
        
        # DEBUG: Print some of the content
        body_text = page.inner_text("body")
        print(f"Body snippet: {body_text[:500]}...")
        
        # INTERACTION: Select Server (Marmara) if possible
        try:
            # The previous attempt showed it might be a select option
            # Check for a select element
            selects = page.query_selector_all("select")
            if selects:
                print(f"Found {len(selects)} select elements.")
                # Try to select by value 409 (Marmara) or by label
                page.select_option("select", value="409")
                print("Selected Marmara (value 409).")
                page.wait_for_load_state("networkidle")
                time.sleep(3)
            else:
                # Fallback to text click if it's not a standard select
                marmara_link = page.get_by_text("Marmara")
                if marmara_link.count() > 0:
                    print(f"Found Marmara text, trying to click first available...")
                    marmara_link.first.click(force=True)
                    page.wait_for_load_state("networkidle")
                    time.sleep(3)
        except Exception as e:
            print(f"Error selecting Marmara: {e}")

        # INTERACTION: Search for item if env var is set
        search_query = os.environ.get("SEARCH_QUERY")
        if search_query:
            print(f"Searching for: {search_query}")
            try:
                # Find input with placeholder 'Eşya ara...'
                search_input = page.locator("#item-search-input")
                if search_input.is_visible():
                    search_input.click()
                    search_input.fill("") # Clear first
                    time.sleep(0.5)
                    search_input.type(search_query, delay=100) # Type like a human
                    time.sleep(0.5)
                    search_input.press("Enter")
                    print("Pressed Enter, waiting for results...")
                    
                    # Wait for network activity to settle
                    page.wait_for_load_state("networkidle")
                    time.sleep(5) # Give generous time for the SPA to filter
                    
                    # DEBUG: Check for dropdown suggestions
                    suggestions = page.locator(".autocomplete-items div, ul.suggestions li, .dropdown-item") # Generic guesses
                    if suggestions.count() > 0:
                        print(f"Found {suggestions.count()} suggestions. Maybe we need to click one?")
                        # suggestions.first.click() 
                    
                    # Check for "No results" message
                    body_text = page.inner_text("body")
                    if "Sonuç bulunamadı" in body_text or "No results" in body_text:
                        print("WARNING: Site says 'No results found'.")
                    
                    # DEBUG: Take screenshot
                    # page.screenshot(path="search_result.png")
                else:
                    print("Search input not visible!")
            except Exception as e:
                print(f"Error searching: {e}")

        # Wait for the table rows to appear.
        try:
            page.wait_for_selector("tbody tr", timeout=15000)
        except:
            print("Timeout waiting for data rows.")

        # INFINITE SCROLL LOGIC
        # Scroll down multiple times to load more items
        print("Scrolling to load more items...")
        try:
            page.hover("tbody") # Focus on the table area
        except:
            pass
            
        for i in range(3): # Scroll a few times
            page.mouse.wheel(0, 10000) 
            time.sleep(1)
            
        # Get page content
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        rows = soup.select("tbody tr") # Assuming standard table structure
        
        data_count = 0
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Ensure server exists
        server_name = "Marmara" # Defaulting for now
        cursor.execute("INSERT OR IGNORE INTO servers (name) VALUES (?)", (server_name,))
        server_id = cursor.execute("SELECT id FROM servers WHERE name=?", (server_name,)).fetchone()[0]

        # 1. Clear old listings for this search query if it exists
        if search_query:
            print(f"Clearing old listings for query: {search_query}")
            # Get item IDs that match the search query
            # We use LIKE %query% to be safe, but ideally we match what we are about to scrape
            # A safer approach is to delete listings for items that contain the search string
            cursor.execute("""
                DELETE FROM listings 
                WHERE item_id IN (
                    SELECT id FROM items WHERE name LIKE ?
                )
            """, (f"%{search_query}%",))
            
            # Also clean up bonuses? No, cascade delete isn't set up in SQLite usually unless enabled.
            # Let's manually clean orphan bonuses later or assume listings deletion handles it if foreign keys are strict.
            # For SQLite simple setup, let's just delete listings. The bonuses table has foreign key to listings.
            # We should probably delete bonuses where listing_id is not in listings.
            cursor.execute("DELETE FROM listing_bonuses WHERE listing_id NOT IN (SELECT id FROM listings)")
            conn.commit()

        print(f"Found {len(rows)} potential rows.")
        
        # Track inserted listings to avoid re-inserting in the same run if duplicates exist in HTML
        inserted_signatures = set()

        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 5: continue 
            
            try:
                # Based on analysis:
                # col[1] contains:
                #   div.font-medium.text-white (Name)
                #   div.text-xs.text-gray-400 (Bonuses -> spans)
                
                info_col = cols[1]
                
                # Extract Name
                name_div = info_col.find('div', class_=lambda x: x and 'font-medium' in x)
                if not name_div:
                    # Fallback
                    item_name = info_col.get_text(strip=True)
                    bonuses = []
                else:
                    # The name might be mixed with a span (e.g. element power).
                    # We just take the text of the name_div, but we might want to clean it.
                    # name_div.get_text(strip=True) -> "Dolunay Kılıcı+9Karanlığın gücü 7..."
                    # The span inside name_div is usually the elemental power.
                    # Let's extract the span text separately if we want, or just keep it in the name.
                    # User wanted "separate".
                    
                    # Strategy: Get only the direct text of name_div? 
                    # BeautifulSoup direct text is hard if mixed.
                    # Let's take the full text of name_div as the name for now, 
                    # but if there is a span inside name_div, maybe treat it as a bonus?
                    # The HTML shows: Dolunay Kılıcı+9 <span class='text-purple-800...'>Karanlığın gücü...</span>
                    
                    # Let's extract spans inside name_div as "special" bonuses
                    name_spans = name_div.find_all('span')
                    special_bonuses = [s.get_text(strip=True) for s in name_spans]
                    
                    # Remove spans to get pure name
                    for s in name_spans:
                        s.extract()
                    item_name = name_div.get_text(strip=True)
                
                # Extract Bonuses (Standard)
                bonus_div = info_col.find('div', class_=lambda x: x and 'text-xs' in x and 'text-gray-400' in x)
                bonuses = []
                
                # Add special bonuses (from name line) to list
                if 'special_bonuses' in locals():
                    bonuses.extend(special_bonuses)
                
                if bonus_div:
                    bonus_spans = bonus_div.find_all('span')
                    for s in bonus_spans:
                        bonuses.append(s.get_text(strip=True))
                else:
                    print(f"DEBUG: No bonus div found for {item_name}")
                    # Debug print classes to see why
                    for d in info_col.find_all('div'):
                         print(f"  DEBUG: Div classes: {d.get('class')}")

                # Filter by search query if provided (Case insensitive check)
                if search_query and search_query.lower() not in item_name.lower():
                    pass

                qty_col = cols[2]
                quantity = parse_price(qty_col.get_text(strip=True))
                if quantity == 0: quantity = 1
                
                yang_col = cols[3]
                yang_text = yang_col.get_text(strip=True)
                yang = parse_price(yang_text)
                
                won_col = cols[4]
                won_text = won_col.get_text(strip=True)
                won = parse_price(won_text)
                
                seller = cols[5].get_text(strip=True) if len(cols) > 5 else "Unknown"
                
                total_yang_value = (won * 100000000) + yang
                
                # Duplicate check within this run
                signature = (item_name, seller, total_yang_value)
                if signature in inserted_signatures:
                    continue
                inserted_signatures.add(signature)

                if item_name:
                    # Insert Item
                    cursor.execute("INSERT OR IGNORE INTO items (name, category) VALUES (?, ?)", (item_name, "General"))
                    item_id_row = cursor.execute("SELECT id FROM items WHERE name=?", (item_name,)).fetchone()
                    
                    if item_id_row:
                        item_id = item_id_row[0]
                        
                        # Always insert new listing since we cleared old ones (or simple insert)
                        cursor.execute("""
                            INSERT INTO listings (server_id, item_id, seller_name, quantity, price_won, price_yang, total_price_yang)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (server_id, item_id, seller, quantity, won, yang, total_yang_value))
                        
                        listing_id = cursor.lastrowid
                        
                        # Insert Bonuses
                        if bonuses:
                            print(f"DEBUG: Inserting {len(bonuses)} bonuses for listing {listing_id}: {bonuses}")
                            for bonus in bonuses:
                                if not bonus: continue
                                cursor.execute("INSERT INTO listing_bonuses (listing_id, bonus_name, bonus_value) VALUES (?, ?, ?)", 
                                            (listing_id, bonus, ""))
                        else:
                            print(f"DEBUG: No bonuses to insert for {item_name}")
                            
                        data_count += 1
                        print(f"Scraped: {item_name} (Bonuses: {len(bonuses)})")

            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error parsing row: {e}")
                continue

                
        conn.commit()
        conn.close()
        browser.close()
        print(f"Scraping complete. Inserted {data_count} listings.")

if __name__ == "__main__":
    # init_db()
    scrape_store()