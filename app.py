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
    """Create the inventory table if it doesn't already exist."""
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        conn.execute(
            "CREATE TABLE inventory (\n"
            "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "    item_name TEXT NOT NULL,\n"
            "    quantity INTEGER NOT NULL\n"
            ")"
        )
        conn.commit()
        conn.close()


@app.route('/')
def dashboard():
    """Display the dashboard showing items grouped by stock level."""
    init_db()
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM inventory').fetchall()
    conn.close()

    # Define threshold for low stock
    low_threshold = 5
    needs_to_buy = []
    low_items = []
    good_items = []

    for item in items:
        qty = item['quantity']
        if qty <= 0:
            needs_to_buy.append(item)
        elif qty < low_threshold:
            low_items.append(item)
        else:
            good_items.append(item)

    return render_template(
        'dashboard.html',
        needs_to_buy=needs_to_buy,
        low_items=low_items,
        good_items=good_items,
    )


@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    """Display and process the inventory update form."""
    init_db()
    conn = get_db_connection()
    if request.method == 'POST':
        # Update the quantity of an existing item
        item_id = request.form.get('id')
        quantity = request.form.get('quantity')
        if item_id and quantity is not None:
            conn.execute(
                'UPDATE inventory SET quantity = ? WHERE id = ?',
                (int(quantity), int(item_id)),
            )
            conn.commit()
    items = conn.execute('SELECT * FROM inventory').fetchall()
    conn.close()
    return render_template('update.html', items=items)


@app.route('/add', methods=['POST'])
def add_item():
    """Handle adding a new item to the inventory."""
    init_db()
    conn = get_db_connection()
    item_name = request.form.get('item_name')
    quantity = request.form.get('quantity')
    if item_name and quantity is not None:
        conn.execute(
            'INSERT INTO inventory (item_name, quantity) VALUES (?, ?)',
            (item_name.strip(), int(quantity)),
        )
        conn.commit()
    conn.close()
    return redirect(url_for('inventory'))


if __name__ == '__main__':
    # Enable debug mode for development convenience. In production, disable debug.
    app.run(debug=True, host='0.0.0.0', port=5000)
