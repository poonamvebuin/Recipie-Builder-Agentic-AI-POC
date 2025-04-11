import streamlit as st

def add_item_to_cart(product, quantity):
    existing = next((item for item in st.session_state.cart_items 
                     if item['Product_name'] == product["Product_name"]), None)
    price = float(product["Price"].replace("Rs", "").strip())

    if existing:
        existing["Quantity"] += quantity
        existing["Total_price"] = existing["Quantity"] * price
    else:
        st.session_state.cart_items.append({
            "Product_name": product["Product_name"],
            "Description": product["Description"],
            "Category": product["Category"],
            "Brand": product["Brand"],
            "Price": price,
            "Weight": product["Weight"],
            "Quantity": quantity,
            "Total_price": price * quantity
        })

def display_cart_summary():
    total = 0
    lines = []
    for item in st.session_state.cart_items:
        lines.append(f"{item['Quantity']} x {item['Product_name']} ({item['Brand']}) - {item['Total_price']} Rs")
        total += item['Total_price']
    lines.append(f"**Total: {total} Rs**")
    return lines
