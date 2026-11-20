import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import sqlite3
import os
from datetime import datetime
from playwright.sync_api import sync_playwright
import time

# Config
MAX_PRICE = 20.0
DB_PATH = "cart.db"
COOKIES_PATH = "cookies.json"

st.set_page_config(page_title="eBay Deal Bot", layout="wide")

# DB Setup for digital Warenkorb
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cart
                 (id INTEGER PRIMARY KEY, item_id TEXT UNIQUE, title TEXT, price REAL, shipping REAL, 
                  image_url TEXT, url TEXT, type TEXT, status TEXT, saved_at TEXT)''')
    conn.commit()
    conn.close()

init_db()

def save_to_cart(item):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO cart (item_id, title, price, shipping, image_url, url, type, status, saved_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
              (item['id'], item['title'], item['price'], item['shipping'], item['image'], item['url'], item['type'], 'gespeichert', datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_cart():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM cart ORDER BY saved_at DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def update_status(item_id, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE cart SET status = ? WHERE item_id = ?", (status, item_id))
    conn.commit()
    conn.close()

# Simple eBay search scraper (for demo; use API for production)
def search_ebay(keywords, max_price=MAX_PRICE):
    # Note: Scraping is fragile and against ToS. Prefer official Browse API.
    url = f"https://www.ebay.de/sch/i.html?_nkw={keywords.replace(' ', '+')}&_sop=15&LH_BIN=0"  # sort by ending soon or new
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = []
        for item in soup.select('.s-item')[:15]:  # limit
            title_el = item.select_one('.s-item__title')
            price_el = item.select_one('.s-item__price')
            link_el = item.select_one('.s-item__link')
            img_el = item.select_one('.s-item__image-img')
            if not title_el or not price_el or not link_el:
                continue
            title = title_el.get_text(strip=True)
            if title == "Shop on eBay":
                continue
            price_text = price_el.get_text(strip=True).replace('€', '').replace(',', '.').split()[0]
            try:
                price = float(price_text)
            except:
                continue
            # Shipping rough estimate
            shipping = 0.0
            ship_el = item.select_one('.s-item__shipping, .s-item__logisticsCost')
            if ship_el:
                ship_text = ship_el.get_text(strip=True)
                if 'Gratis' in ship_text or 'Kostenlos' in ship_text:
                    shipping = 0.0
                elif '€' in ship_text:
                    try:
                        shipping = float(ship_text.replace('€', '').replace(',', '.').split()[0])
                    except:
                        shipping = 3.0  # default
            total = price + shipping
            if total > max_price:
                continue
            url = link_el['href']
            image = img_el['src'] if img_el and img_el.get('src') else ''
            item_id = url.split('/itm/')[-1].split('?')[0] if '/itm/' in url else url[-12:]
            # Determine type roughly
            type_ = 'auction'  # default
            if 'Sofort-Kaufen' in str(item) or 'Buy It Now' in str(item):
                type_ = 'both' if 'Gebote' in str(item) else 'bin'
            items.append({
                'id': item_id,
                'title': title,
                'price': price,
                'shipping': shipping,
                'total': total,
                'image': image,
                'url': url,
                'type': type_
            })
        return items
    except Exception as e:
        st.error(f"Suchfehler: {e}")
        return []

# Playwright action (bid or buy)
def perform_action(url, action='bid', max_bid=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # visible for user confirmation if needed
        context = browser.new_context()
        if os.path.exists(COOKIES_PATH):
            with open(COOKIES_PATH) as f:
                cookies = json.load(f)
            context.add_cookies(cookies)
        page = context.new_page()
        page.goto(url)
        time.sleep(2)
        # Save cookies after login if first time
        if not os.path.exists(COOKIES_PATH):
            st.info("Bitte logge dich im geöffneten Browser bei eBay ein, dann schließe das Fenster und starte neu.")
            # In practice, wait for user or implement better login flow
            time.sleep(30)  # give time to login
            cookies = context.cookies()
            with open(COOKIES_PATH, 'w') as f:
                json.dump(cookies, f)
        if action == 'bid':
            # Implement bid logic: find bid input, enter amount, confirm
            # This is placeholder - needs precise selectors for eBay.de
            try:
                page.fill('input[name*="bid"], #bidAmount, input[aria-label*="Gebot"]', str(max_bid or 20))
                page.click('button:has-text("Bieten"), input[value*="Bieten"]')
                st.success("Gebot platziert! (Platzhalter - Selektoren anpassen)")
            except Exception as e:
                st.error(f"Bieten fehlgeschlagen: {e}")
        elif action == 'buy':
            try:
                page.click('a:has-text("Sofort-Kaufen"), button:has-text("Sofort-Kaufen"), #binBtn')
                # Confirm checkout steps
                st.success("Kauf gestartet! (Platzhalter)")
            except Exception as e:
                st.error(f"Kauf fehlgeschlagen: {e}")
        browser.close()

# UI
st.title("🚀 eBay Deal Bot - Max 20€ + Versand")
st.caption("Kontinuierliche Deals | Digitaler Warenkorb | Ja bieten / Ja kaufen mit Bestätigung")

# Sidebar config
with st.sidebar:
    st.header("Einstellungen")
    keywords = st.text_input("Suchbegriffe", "Laptop, Smartphone, Spielzeug")
    max_p = st.number_input("Max Preis + Versand (€)", value=20.0)
    if st.button("Suche aktualisieren"):
        st.session_state['deals'] = search_ebay(keywords, max_p)
    st.markdown("---")
    st.subheader("Warenkorb")
    cart = get_cart()
    for row in cart:
        st.write(f"{row[2][:40]}... | {row[8]} | €{row[3]}")

# Main deals
if 'deals' not in st.session_state:
    st.session_state['deals'] = search_ebay(keywords)

deals = st.session_state.get('deals', [])
st.subheader(f"Aktuelle Deals ({len(deals)})")

for item in deals:
    col1, col2 = st.columns([1, 3])
    with col1:
        if item['image']:
            st.image(item['image'], width=150)
        else:
            st.write("Kein Bild")
    with col2:
        st.markdown(f"**{item['title']}**")
        st.write(f"Preis: {item['price']}€ + Versand: {item['shipping']}€ = **{item['total']}€**")
        st.write(f"Typ: {item['type']} | [Link]({item['url']})")
        # Conditional buttons
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("💾 Speichern", key=f"save_{item['id']}"):
                save_to_cart(item)
                st.success("Im Warenkorb gespeichert!")
                st.rerun()
        if item['type'] in ['auction', 'both']:
            with btn_col2:
                if st.button("✅ Ja bieten", key=f"bid_{item['id']}"):
                    perform_action(item['url'], 'bid', max_p)
                    update_status(item['id'], 'geboten')
                    st.rerun()
        if item['type'] in ['bin', 'both']:
            with btn_col3:
                if st.button("🛒 Ja kaufen", key=f"buy_{item['id']}"):
                    perform_action(item['url'], 'buy')
                    update_status(item['id'], 'gekauft')
                    st.rerun()

st.info("Tipp: Für echte Automatisierung die Playwright-Selektoren in app.py an die aktuelle eBay.de Seite anpassen. Einmalig einloggen für Session.")

# Auto refresh option
if st.button("🔄 Deals neu laden"):
    st.session_state['deals'] = search_ebay(keywords, max_p)
    st.rerun()
