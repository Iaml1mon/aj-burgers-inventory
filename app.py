"""AJ Burgers Inventory Management Application

This Flask application provides a self‑contained, responsive inventory management system for a food
truck.  It offers a dashboard overview, bulk updating of stock levels, and an interactive order
generation page with WhatsApp sharing.  The UI avoids external CDN dependencies so it works
reliably even on networks that block third‑party resources.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from urllib.parse import quote


app = Flask(__name__)
app.secret_key = "replace_with_a_random_secret"


def get_db_connection():
    """Create a connection to the SQLite database and ensure row access by name."""
    conn = sqlite3.connect("inventory.db")
    conn.row_factory = sqlite3.Row
    return conn


# Default thresholds and initial inventory definitions.  These reflect the AJ Burgers shopping
# checklist.  Each item belongs to a category and has an associated threshold indicating when
# reordering should occur.
DEFAULT_INVENTORY = {
    "Buns & Chips": {
        "Chips": 20,
        "Buns": 30,
    },
    "Veggies": {
        "Lettuce": 10,
        "Tomatoes": 10,
        "Onions": 10,
        "Pickles": 5,
        "Beetroot": 5,
    },
    "Meats & Poultry": {
        "Chicken": 10,
        "Beef": 10,
        "Wagyu": 5,
        "Eggs": 24,
    },
    "Cheeses": {
        "Block": 5,
        "Shredded Cheese": 5,
        "Butter": 5,
    },
    "Drinks": {
        "Coke": 24,
        "Coke Zero": 24,
        "Solo": 24,
        "Fanta": 24,
        "Water": 24,
    },
    "Sauces & Condiments": {
        "Ketchup": 5,
        "Chilli": 5,
        "Mustard": 5,
        "Mayonnaise": 5,
        "BBQ sauce": 5,
        "Special Sauce": 5,
    },
    "Packaging & Delivery": {
        "Burger boxes": 50,
        "Uber bags": 20,
        "Plastic Bags": 50,
    },
    "Cleaning Materials": {
        "Dish soap": 2,
        "Hand Soap": 2,
        "Floor Cleaning Liquid": 2,
        "Paper towels": 12,
        "Silver Scrubbers": 5,
        "Lemon Juice": 5,
        "Gloves": 20,
        "Sprays": 2,
    },
    "Stationery": {
        "Order pads": 5,
        "Pens": 12,
        "Markers": 6,
        "Receipt rolls": 10,
        "Staplers": 2,
    },
    "Oils & Gas": {
        "Cooking oil": 10,
        "Gas": 3,
        "Small Gas": 3,
    },
    "Salt & Spices": {
        "Chicken Salt": 5,
        "Normal Salt": 5,
        "Tasting Salt": 5,
        "Ground Pepper": 5,
    },
    "Others": {
        # Add any miscellaneous items here with reasonable thresholds.
    },
}


def init_db():
    """Initialise the SQLite database with the default inventory if it doesn't exist."""
    if os.path.exists("inventory.db"):
        return
    conn = get_db_connection()
    conn.execute(
        "CREATE TABLE inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, category TEXT, quantity INTEGER, threshold INTEGER)"
    )
    for category, items in DEFAULT_INVENTORY.items():
        for item_name, threshold in items.items():
            # Default quantity is zero for new items
            conn.execute(
                "INSERT INTO inventory (item_name, category, quantity, threshold) VALUES (?, ?, ?, ?)",
                (item_name, category, 0, threshold),
            )
    conn.commit()
    conn.close()


@app.before_request
def ensure_db():
    """Ensure the database exists before handling any requests."""
    init_db()


@app.route("/")
def dashboard():
    """Display the dashboard overview with summary metrics and a category breakdown."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM inventory").fetchall()
    conn.close()

    # Compute summary metrics
    total_items = len(rows)
    low_items = sum(1 for row in rows if row["quantity"] < row["threshold"] and row["quantity"] > 0)
    out_of_stock = sum(1 for row in rows if row["quantity"] == 0)
    good_items = total_items - low_items - out_of_stock

    # Group items by category and stock status
    grouped = {}
    for row in rows:
        cat = row["category"]
        status = (
            "needs"
            if row["quantity"] == 0
            else "low"
            if row["quantity"] < row["threshold"]
            else "good"
        )
        grouped.setdefault(cat, {"needs": [], "low": [], "good": []})
        grouped[cat][status].append(row)

    summary = {
        "total": total_items,
        "low": low_items,
        "out": out_of_stock,
        "good": good_items,
    }
    return render_template("dashboard.html", summary=summary, grouped=grouped)


@app.route("/inventory", methods=["GET", "POST"])
def inventory():
    """Display inventory details and allow bulk updating of quantities and thresholds."""
    conn = get_db_connection()
    if request.method == "POST":
        # Bulk update.  Expect form fields like quantity_<id> and threshold_<id>
        for key, value in request.form.items():
            if key.startswith("quantity_"):
                try:
                    item_id = int(key.split("_")[1])
                except (IndexError, ValueError):
                    continue
                try:
                    quantity = int(value)
                except ValueError:
                    quantity = 0
                # threshold may not exist if user didn't change
                threshold_value = request.form.get(f"threshold_{item_id}")
                if threshold_value is not None:
                    try:
                        threshold = int(threshold_value)
                    except ValueError:
                        threshold = 0
                    conn.execute(
                        "UPDATE inventory SET quantity = ?, threshold = ? WHERE id = ?",
                        (quantity, threshold, item_id),
                    )
                else:
                    conn.execute(
                        "UPDATE inventory SET quantity = ? WHERE id = ?",
                        (quantity, item_id),
                    )
        conn.commit()
        conn.close()
        flash("Inventory updated successfully!", "success")
        return redirect(url_for("inventory"))

    # GET request: fetch items sorted by category
    rows = conn.execute(
        "SELECT * FROM inventory ORDER BY category, item_name"
    ).fetchall()
    conn.close()
    return render_template("update.html", items=rows)


@app.route("/order", methods=["GET", "POST"])
def order():
    """Display items below or equal to threshold and allow the user to generate an order message."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM inventory ORDER BY category, item_name"
    ).fetchall()
    conn.close()
    # Filter for low or out of stock items
    order_items = []
    for row in rows:
        if row["quantity"] <= row["threshold"]:
            # Suggest ordering enough to double the threshold minus current quantity
            suggested = max(row["threshold"] * 2 - row["quantity"], row["threshold"])
            order_items.append(
                {
                    "id": row["id"],
                    "name": row["item_name"],
                    "category": row["category"],
                    "current_qty": row["quantity"],
                    "threshold": row["threshold"],
                    "suggested_order": suggested,
                }
            )

    if request.method == "POST":
        # Build order message from submitted quantities and notes
        lines = []
        for item in order_items:
            qty_str = request.form.get(f"order_qty_{item['id']}")
            note = request.form.get(f"note_{item['id']}")
            try:
                qty = int(qty_str) if qty_str else 0
            except ValueError:
                qty = 0
            if qty > 0:
                line = f"{item['name']} x {qty}"
                if note:
                    line += f" ({note})"
                lines.append(line)
        if not lines:
            flash("No items selected for ordering.", "warning")
            return redirect(url_for("order"))
        message = "ORDER LIST - AJ BURGERS\n" + "\n".join(lines)
        encoded = quote(message)
        whatsapp_url = f"https://api.whatsapp.com/send?text={encoded}"
        return render_template(
            "order_message.html", order_message=message, whatsapp_url=whatsapp_url
        )
    return render_template("order.html", order_items=order_items)


if __name__ == "__main__":
    app.run(debug=True)