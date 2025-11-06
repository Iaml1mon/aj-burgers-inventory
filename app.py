"""
AJ Burgers Inventory Management Application

This simple Flask app provides a web interface for tracking inventory for a food truck.
Users can view a dashboard that classifies items by stock level and update quantities
or add new items. Data is persisted in a local SQLite database so that it survives
across sessions.

To run the app:

    pip install -r requirements.txt
    python app.py

Then visit http://localhost:5000 in your browser.
"""

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for


app = Flask(__name__)

# Path to the SQLite database file
DATABASE = os.path.join(os.path.dirname(__file__), 'inventory.db')


def get_db_connection():
    """Return a connection to the SQLite database with row factory set."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initialize the SQLite database.  If the database file does not exist, this
    function creates a new `inventory` table with columns for name, category,
    quantity and threshold.  It also populates the table with a default set
    of items grouped by category defined in `DEFAULT_INVENTORY`.  Each item
    starts with a quantity of 0 so that the dashboard will immediately
    classify them as needing to be bought.
    """
    if os.path.exists(DATABASE):
        # Nothing to do if the database already exists
        return

    conn = get_db_connection()
    # Create table with category and threshold columns
    conn.execute(
        "CREATE TABLE IF NOT EXISTS inventory (\n"
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
        "    item_name TEXT NOT NULL,\n"
        "    category TEXT NOT NULL,\n"
        "    quantity INTEGER NOT NULL,\n"
        "    threshold INTEGER NOT NULL\n"
        ")"
    )

    # Populate the table with default inventory items if empty
    cursor = conn.execute("SELECT COUNT(*) as count FROM inventory")
    count = cursor.fetchone()["count"]
    if count == 0:
        # Insert default items with quantity 0
        for category, items in DEFAULT_INVENTORY.items():
            # Determine a sensible default threshold per category
            default_threshold = DEFAULT_THRESHOLDS.get(category, 5)
            for item in items:
                conn.execute(
                    "INSERT INTO inventory (item_name, category, quantity, threshold) VALUES (?, ?, ?, ?)",
                    (item, category, 0, default_threshold),
                )
    conn.commit()
    conn.close()


# Default inventory grouped by category.  These values come from the user‑provided
# restaurant shopping checklist.  If you need to modify these defaults in the
# future, update this dictionary accordingly.
DEFAULT_INVENTORY = {
    "Buns & Chips": ["Chips", "Buns"],
    "Veggies": ["Lettuce", "Tomatoes", "Onions", "Pickles", "Beetroot"],
    "Meats & Poultry": ["Chicken", "Beef", "Wagyu", "Eggs"],
    "Cheeses": ["Block", "Shredded Cheese", "Butter"],
    "Drinks": ["Coke", "Coke Zero", "Solo", "Fanta", "Water"],
    "Sauces & Condiments": ["Ketchup", "Chilli", "Mustard", "Mayonnaise", "BBQ sauce", "Special Sauce"],
    "Packaging & Delivery": ["Burger boxes", "Uber bags", "Plastic Bags"],
    "Cleaning Materials": ["Dish soap", "Hand Soap", "Floor Cleaning Liquid", "Paper towels", "Silver Scrubbers", "Lemon Juice", "Gloves", "Sprays"],
    "Stationery": ["Order pads", "Pens", "Markers", "Receipt rolls", "Staplers"],
    "Oils & Gas": ["Cooking oil", "Gas", "Small Gas"],
    "Salt & Spices": ["Chicken Salt", "Normal Salt", "Tasting Salt", "Ground Pepper"],
    "Others": [],
}

# Suggested default reorder thresholds per category.  These values determine when
# an item is considered "low stock" on the dashboard.  Adjust these to suit
# your business needs.  Any category not present here defaults to 5.
DEFAULT_THRESHOLDS = {
    "Buns & Chips": 10,
    "Veggies": 5,
    "Meats & Poultry": 5,
    "Cheeses": 3,
    "Drinks": 24,
    "Sauces & Condiments": 6,
    "Packaging & Delivery": 20,
    "Cleaning Materials": 10,
    "Stationery": 10,
    "Oils & Gas": 5,
    "Salt & Spices": 5,
    "Others": 5,
}


@app.route('/')
def dashboard():
    """
    Render the inventory dashboard.  Items are grouped by category and
    subdivided into three stock statuses: needs to buy (quantity <= 0), low
    stock (quantity below its defined threshold) and good (quantity >= threshold).
    The resulting structure `grouped_items` is a dictionary keyed by category
    mapping to another dict with keys 'needs', 'low' and 'good'.
    """
    init_db()
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM inventory ORDER BY category, item_name').fetchall()
    conn.close()

    # Prepare grouped data
    grouped_items: dict[str, dict[str, list]] = {}
    for item in items:
        category = item['category']
        grouped_items.setdefault(category, {'needs': [], 'low': [], 'good': []})
        qty = item['quantity']
        threshold = item['threshold']
        if qty <= 0:
            grouped_items[category]['needs'].append(item)
        elif qty < threshold:
            grouped_items[category]['low'].append(item)
        else:
            grouped_items[category]['good'].append(item)

    return render_template(
        'dashboard.html',
        grouped_items=grouped_items,
    )


@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    """Display and process the inventory update form."""
    init_db()
    conn = get_db_connection()
    if request.method == 'POST':
        # Determine if this is an update to an existing item or threshold
        if 'update_id' in request.form:
            # Update the quantity (and optionally threshold) of an existing item
            item_id = request.form.get('update_id')
            quantity = request.form.get('quantity')
            threshold = request.form.get('threshold')
            if item_id and quantity is not None:
                # Only update the fields provided
                if threshold:
                    conn.execute(
                        'UPDATE inventory SET quantity = ?, threshold = ? WHERE id = ?',
                        (int(quantity), int(threshold), int(item_id)),
                    )
                else:
                    conn.execute(
                        'UPDATE inventory SET quantity = ? WHERE id = ?',
                        (int(quantity), int(item_id)),
                    )
                conn.commit()
        # When adding a new item, the form is handled by the /add route
    items = conn.execute('SELECT * FROM inventory ORDER BY category, item_name').fetchall()
    conn.close()
    # Provide categories list for the add form
    categories = list(DEFAULT_INVENTORY.keys())
    return render_template('update.html', items=items, categories=categories)


@app.route('/add', methods=['POST'])
def add_item():
    """Handle adding a new item to the inventory."""
    init_db()
    conn = get_db_connection()
    item_name = request.form.get('item_name')
    quantity = request.form.get('quantity')
    category = request.form.get('category')
    threshold = request.form.get('threshold')
    if item_name and quantity is not None and category:
        # Use provided threshold or default one for the category
        if threshold:
            th_value = int(threshold)
        else:
            th_value = DEFAULT_THRESHOLDS.get(category, 5)
        conn.execute(
            'INSERT INTO inventory (item_name, category, quantity, threshold) VALUES (?, ?, ?, ?)',
            (item_name.strip(), category, int(quantity), th_value),
        )
        conn.commit()
    conn.close()
    return redirect(url_for('inventory'))


if __name__ == '__main__':
    # Enable debug mode for development convenience. In production, disable debug.
    app.run(debug=True, host='0.0.0.0', port=5000)
