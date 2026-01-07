# Price Monitoring Agent

This repository contains a starter Python script (`price_monitor_agent.py`) that
implements a basic price monitoring agent.  The agent can track multiple
products from different e‑commerce websites, store historical prices in a
database, compute a 52‑week trailing low and send a notification whenever a
product reaches a new low price.

> **Note**: This is **not** a full production solution.  It is intended to
demonstrate the core architecture and logic required.  You will need to
customise the scraping functions, configure credentials for notifications and
potentially deploy the agent to a server or scheduler to run it on a
recurring basis.

## How It Works

1. **Configuration**: Define the products you want to monitor in
   `price_monitor_agent.py` by listing each product's SKU (or other unique
   identifier), name and URL.  Add more products as needed.
2. **Scraping**: For each product, the script calls a site‑specific function
   that fetches the current price, shipping cost, availability and site name.
   The default implementation uses a placeholder function that returns dummy
   values.  You must replace this with real logic (using Python libraries like
   `requests` and `BeautifulSoup`, or headless browsers like Playwright) to
   retrieve data from your desired websites.
3. **Database**: Price data is stored in a local SQLite database (`price_history.db`)
   for each polling run.  Each record includes the product SKU, site, price,
   shipping cost, availability flag and timestamp.  You can switch to a more
   scalable database (e.g. PostgreSQL with TimescaleDB) by replacing the
   database functions.
4. **Trailing Low Calculation**: The script computes a 52‑week trailing low
   price for each product by taking the minimum price recorded in the last
   52 weeks.  If the current price is lower than the stored low (and the
   product is available), it triggers a notification.
5. **Notifications**: If Twilio credentials are configured, the agent sends
   an SMS alert via Twilio.  Otherwise, it prints a notification to the
   console.  You can replace this logic with email, push notifications or
   another alerting mechanism.
6. **Scheduling**: The script checks each product once when executed.  To
   monitor prices continuously, schedule the script to run periodically via
   `cron`, a task scheduler like Airflow or a serverless function.

## Setup

1. Clone or download this repository.
2. Ensure you have Python 3.7+ installed.
3. Install any dependencies:

   ```bash
   pip install twilio
   # Additionally install libraries for scraping (e.g. requests, beautifulsoup4)
   ```

4. Edit `price_monitor_agent.py`:

   - Add your products to `TRACKED_PRODUCTS`.
   - Implement real scraping logic in the `fetch_price_from_example` function
     or add new functions for each site you plan to monitor.  Map domain
     prefixes to the appropriate functions in the `SCRAPER_MAPPING` dictionary.
   - Configure Twilio or modify `send_notification` to use your preferred
     notification channel.

5. Run the script manually:

   ```bash
   python price_monitor_agent.py
   ```

   The first run will initialise the database.  On subsequent runs, it will
   insert new price records and notify you if the price falls below the
   trailing low.

6. To run the agent periodically, set up a cron job or use a scheduler.  For
   example, to run every 30 minutes using cron:

   ```cron
   */30 * * * * /usr/bin/python /path/to/price_monitor_agent.py
   ```

## Limitations and Considerations

* **Legal Compliance**: Always check the terms of service and robots.txt for
  each website you intend to scrape.  Use official APIs where possible to
  respect site policies.
* **Scalability**: SQLite is suitable for small to medium workloads.  For a
  larger number of products or higher polling frequency, consider migrating
  to PostgreSQL + TimescaleDB or another time‑series database.
* **Error Handling**: The skeleton script includes minimal error handling.
  Extend it to handle network failures, retries, and site‑specific parsing
  errors gracefully.
* **Notification Channels**: SMS via Twilio is just one option.  You may
  prefer email (SendGrid), push notifications or Slack messages depending on
  your workflow.

## License

This project is provided for educational purposes.  You are free to adapt
and use it in your own projects under the terms of the MIT license.
