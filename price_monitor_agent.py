#!/usr/bin/env python3
"""
price_monitor_agent.py

This script implements a simple price monitoring agent.  It collects prices for a set of
products from configurable e‑commerce sites, tracks historical prices, computes a 52‑week
trailing low and sends notifications when a new low is observed.

This is intended as a starting point for a more robust system.  You will need to replace
the placeholder scraping functions with actual web scraping or API calls for your target
sites and provide credentials for any external services (e.g. Twilio for SMS
notifications).  See README.md for details.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

# Optional: if you want to use the Twilio API for SMS notifications, install the
# `twilio` package and configure the SID, token and phone numbers below.  Otherwise,
# you can implement your own notification logic in the `send_notification` function.
try:
    from twilio.rest import Client
except ImportError:
    Client = None  # type: ignore

###############################################################################
# Configuration

# SQLite database file used to store price history.  For production use, consider
# using PostgreSQL with TimescaleDB or another time‑series database.
DB_PATH = "price_history.db"

# Products to track.  Each entry should include at least a `sku` (or other unique
# identifier) and a `url` for the product page.  Add as many products as you like.
TRACKED_PRODUCTS: List[Dict[str, str]] = [
    {
        "sku": "B08N5WRWNW",
        "name": "Example Product A",
        "url": "https://example.com/product_A",
    },
    {
        "sku": "B09ABCDE123",
        "name": "Example Product B",
        "url": "https://example2.com/product_B",
    },
        {
            "sku": "B0DWRBVDN6",
            "name": "Amazon Kindle Scribe Colorsoft 32GB",
            "url": "https://www.amazon.com/dp/B0DWRBVDN6",
        },

    # Add additional products here...
]

# Twilio notification configuration.  If you wish to send SMS alerts, fill in the
# following constants with your Twilio account SID, auth token, and phone numbers.
# If `twilio.rest.Client` is not available or these values are left blank, the
# script will print notifications to the console instead.
TWILIO_ACCOUNT_SID: str = ""
 
TWILIO_AUTH_TOKEN: str = ""
TWILIO_FROM_NUMBER: str = ""
TWILIO_TO_NUMBER: str = ""

###############################################################################
# Database functions

def init_db() -> None:
    """Initialise the price history database if it does not already exist."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS price_history (
                sku TEXT,
                site TEXT,
                price REAL,
                shipping REAL,
                available INTEGER,
                ts TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_price_history_sku_ts
            ON price_history (sku, ts)
            """
        )
        conn.commit()


def store_price(
    sku: str, site: str, price: float, shipping: float, available: bool
) -> None:
    """Store a single price record in the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO price_history (sku, site, price, shipping, available, ts)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                sku,
                site,
                price,
                shipping,
                1 if available else 0,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()


def get_trailing_low(sku: str, weeks: int = 52) -> Optional[float]:
    """Return the lowest price observed for the given SKU within the last `weeks` weeks."""
    cutoff = datetime.utcnow() - timedelta(weeks=weeks)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT MIN(price) FROM price_history
            WHERE sku = ?
              AND ts >= ?
            """,
            (sku, cutoff.isoformat()),
        )
        row = cursor.fetchone()
        if row and row[0] is not None:
            return float(row[0])
        return None


###############################################################################
# Notification logic

def send_notification(product: Dict[str, str], price: float) -> None:
    """
    Notify the user that a product's price has reached a new 52‑week low.

    If Twilio credentials are configured, this sends an SMS.  Otherwise, it prints
    the notification to stdout.
    """
    message_body = (
        f"Price alert: '{product['name']}' (SKU {product['sku']}) has a new low price "
        f"of {price:.2f}. See {product['url']} for details."
    )
    if Client and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER and TWILIO_TO_NUMBER:
        try:
            twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            twilio_client.messages.create(
                body=message_body,
                from_=TWILIO_FROM_NUMBER,
                to=TWILIO_TO_NUMBER,
            )
            print(f"Notification sent via Twilio: {message_body}")
        except Exception as exc:
            print(f"Failed to send SMS via Twilio: {exc}")
            print(f"Notification message: {message_body}")
    else:
        # Fallback: print to console
        print(f"[NOTIFICATION] {message_body}")


###############################################################################
# Scraping and price-fetching logic

def fetch_price_from_example(url: str) -> Dict[str, object]:
    """
    Placeholder function to fetch price information from a product URL.

    Replace this function with code that actually scrapes the target e‑commerce
    website or calls its API to retrieve price, shipping cost, availability, and
    site name.  The return value should be a dictionary with keys:

      - price (float)
      - shipping (float)
      - available (bool)
      - site (str)

    Example:
        return {
            "price": 199.99,
            "shipping": 0.00,
            "available": True,
            "site": "ExampleSite",
        }
    """
    # This example returns dummy values.  For real use, implement scraping logic.
    return {
        "price": 199.99,
        "shipping": 0.00,
        "available": True,
        "site": "ExampleSite",
    }


# Mapping from domain prefixes to scraping functions.  The keys should be substrings
# of product URLs that uniquely identify which scraper to use.  You can add more
# domains and corresponding functions as needed.
SCRAPER_MAPPING: Dict[str, Callable[[str], Dict[str, object]]] = {
    "example.com": fetch_price_from_example,
    "example2.com": fetch_price_from_example,
    # Add real domain-specific functions here...
}

###############################################################################
# Main logic

def check_product(product: Dict[str, str]) -> None:
    """Fetch the current price for a product, store it, and notify if it's a new low."""
    url = product["url"]
    scraper_func: Optional[Callable[[str], Dict[str, object]]] = None
    # Determine which scraper to use based on URL substring
    for domain_prefix, func in SCRAPER_MAPPING.items():
        if domain_prefix in url:
            scraper_func = func
            break
    if scraper_func is None:
        print(f"No scraper defined for URL: {url}")
        return

    try:
        result = scraper_func(url)
    except Exception as exc:
        print(f"Error fetching price for {product['name']} ({url}): {exc}")
        return

    # Extract fields from result
    price = float(result.get("price", float("inf")))
    shipping = float(result.get("shipping", 0.0))
    available = bool(result.get("available", False))
    site = str(result.get("site", "UnknownSite"))

    # Store the price in the database
    store_price(product["sku"], site, price, shipping, available)

    # Check if this price is a new 52‑week low
    trailing_low = get_trailing_low(product["sku"], weeks=52)
    if trailing_low is None or (available and price < trailing_low):
        # Notify user of new low
        send_notification(product, price)


def run_monitoring_loop() -> None:
    """Initialises the database and checks all tracked products once."""
    init_db()
    for product in TRACKED_PRODUCTS:
        check_product(product)


if __name__ == "__main__":
    # When run directly, perform a single monitoring pass.
    run_monitoring_loop()
