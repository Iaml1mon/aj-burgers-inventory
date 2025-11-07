# AJ Burgers Inventory Management Overhaul

This project provides a modern, self‑contained inventory management web app for **AJ Burgers**. Built with Python and Flask, it lets staff track stock levels, update quantities in bulk, and generate purchase orders. The UI is designed to feel like a premium internal tool—no external CDNs required—so it remains functional even when your network blocks third‑party resources.

## Features

* **Dashboard summary** – shows total items, low stock, out of stock and good items at a glance.
* **Category breakdown** – each category card lists items that need replenishment, are low on stock, or are at healthy levels.
* **Bulk update** – update quantities and thresholds for all items at once using a single button.
* **Order Today page** – automatically lists items below threshold, lets you adjust order quantities and notes, and generates a formatted message with a share link to WhatsApp.
* **Responsive and accessible UI** – lightweight CSS with warm colours, sticky headers, and simple interactions works on desktop, tablet and mobile.

## Running Locally

1. Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

2. Start the server:

```bash
python app.py
```

3. Visit `http://localhost:5000` in your browser.

The SQLite database (`inventory.db`) is created automatically on first run and pre‑populated with the default inventory.

## Deployment

To deploy on a service such as Render:

1. Ensure `gunicorn` is in your requirements (already included).
2. Set build command to `pip install -r requirements.txt`.
3. Set start command to `gunicorn app:app`.

Commit all project files to your repository, deploy the latest commit and your updated UI should be live.
