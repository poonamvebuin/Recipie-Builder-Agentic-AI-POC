import streamlit as st
import re

# Function to parse price from strings like '715円' or '税込10% 786円'
def parse_price(price_str):
    if not price_str:  # Check if the string is None or empty
        return 0.0  # Return 0 if invalid
    match = re.search(r"[\d,]+(?:\.\d+)?", price_str)
    if match:
        return float(match.group(0).replace(",", ""))
    return 0.0  # Return 0 if parsing fails

# Function to add an item to the cart
def add_item_to_cart(product, quantity):
    print('2222222222')
    # Check if the product is already in the cart
    existing = next((item for item in st.session_state.cart_items 
                     if item['Product_name'] == product["Product_name"]), None)

    # Parse the base price and price with tax
    price = parse_price(product["Price"])  # Base price

    # Check if 'Tax' is valid before parsing
    tax = product.get("Tax", "")
    price_with_tax = parse_price(tax)  # Price with tax (may be empty)

    if existing:
        # If the item is already in the cart, update its quantity and prices
        existing["Quantity"] += quantity
        existing["Price"] = price
        existing["Price_with_Tax"] = price_with_tax
        existing["Total_price"] = existing["Quantity"] * price
        existing["Total_Price_with_Tax"] = existing["Quantity"] * price_with_tax
    else:
        # If the item is not in the cart, add it
        st.session_state.cart_items.append({
            "Product_name": product["Product_name"],
            "Price": price,
            "Price_with_Tax": price_with_tax,
            "Weight": product["Weight"],
            "Quantity": quantity,
            "Total_price": price * quantity,
            "Total_Price_with_Tax": price_with_tax * quantity
        })

# Function to display the cart summary
def display_cart_summary():
    total_base = 0
    total_with_tax = 0
    lines = []

    for item in st.session_state.cart_items:
        # Calculate the total for both base price and price with tax
        item_total_base = item['Total_price']
        item_total_with_tax = item['Total_Price_with_Tax']

        # Prepare a summary line for each item
        line = (
            f"{item['Quantity']} x {item['Product_name']}\n"
            f"Price: {item['Price']} 円\n"
            f"Price with Tax: {item['Price_with_Tax']} 円"
        )
        lines.append(line)

        # Accumulate the totals
        total_base += item_total_base
        total_with_tax += item_total_with_tax

    # Display the total values for both base price and price with tax
    lines.append("---")
    lines.append(f"**Total price: {total_base} 円**")
    lines.append(f"**Total price with Tax: {total_with_tax} 円**")
    return lines
