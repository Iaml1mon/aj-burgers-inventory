# AJ Burgers Inventory Management

This repository contains a simple Python Flask application for managing inventory for AJ Burgers food truck. The app allows you to:

- View a dashboard highlighting items that **need to be bought**, items **low in stock**, and items that are **all good**.
- Update the quantity of existing items via a web form.
- Add new items to the inventory on the fly.

## Setup

1. Clone the repository (or download the ZIP).
2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   python app.py
   ```

4. Open your browser at `http://localhost:5000` to access the dashboard and update pages.

The inventory is stored in an SQLite database (`inventory.db`) in the project directory, so your data persists across sessions.
