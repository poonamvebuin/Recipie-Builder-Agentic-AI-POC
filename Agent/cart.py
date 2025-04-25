import streamlit as st
import re


def parse_price(price_str):
    if not price_str:
        return 0.0
    matches = re.findall(r"[\d,]+(?:\.\d+)?", price_str)
    if matches:
        return float(matches[-1].replace(",", ""))
    return 0.0


def add_item_to_cart(product, quantity):
    existing = next((item for item in st.session_state.cart_items 
                     if item['Product_name'] == product["Product_name"]), None)

    price = parse_price(product["Price"])

    tax = product.get("Tax", "")
    price_with_tax = parse_price(tax)

    if existing:

        existing["Quantity"] += quantity
        existing["Price"] = price
        existing["Price_with_Tax"] = price_with_tax
        existing["Total_price"] = existing["Quantity"] * price
        existing["Total_Price_with_Tax"] = existing["Quantity"] * price_with_tax
    else:

        st.session_state.cart_items.append({
            "Product_name": product["Product_name"],
            "Price": price,
            "Price_with_Tax": price_with_tax,
            "Weight": product["Weight"],
            "Quantity": quantity,
            "Total_price": price * quantity,
            "Total_Price_with_Tax": price_with_tax * quantity
        })

        
def display_cart_summary():
    total_base = 0
    total_with_tax = 0
    lines = []

    for item in st.session_state.cart_items:

        item_total_base = item['Total_price']
        item_total_with_tax = item['Total_Price_with_Tax']


        line = (
            f"{item['Quantity']} x {item['Product_name']}\n"
            f"Price: {item['Price']} 円\n"
            f"Price with Tax: {item['Price_with_Tax']} 円"
        )
        lines.append(line)


        total_base += item_total_base
        total_with_tax += item_total_with_tax

    lines.append("---")
    lines.append(f"**Total price: {total_base} 円**")
    lines.append(f"**Total price with Tax: {total_with_tax} 円**")
    return lines
