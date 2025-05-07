import re

import streamlit as st


def parse_price(price_str):
    """Parse a price string and convert it to a float.

    This function takes a string representation of a price, extracts the numeric value, and returns it as a float. If the input string is empty or does not contain a valid price, the function returns 0.0.

    Args:
        price_str (str): The string representation of the price to be parsed.

    Returns:
        float: The parsed price as a float. Returns 0.0 if the input is empty or no valid price is found.
    """

    if not price_str:
        return 0.0
    matches = re.findall(r"[\d,]+(?:\.\d+)?", price_str)
    if matches:
        return float(matches[-1].replace(",", ""))
    return 0.0


def add_item_to_cart(product, quantity):
    """Adds an item to the shopping cart, updating the quantity and price if the item already exists.

    Args:
        product (dict): A dictionary containing product details, including 'Product_name', 'Price', 'Tax', and 'Weight'.
        quantity (int): The quantity of the product to add to the cart.

    Returns:
        None: This function modifies the session state directly and does not return a value.

    Raises:
        KeyError: If the product dictionary does not contain the required keys.
        TypeError: If the quantity is not an integer.
    """

    existing = next(
        (
            item
            for item in st.session_state.cart_items
            if item["Product_name"] == product["Product_name"]
        ),
        None,
    )

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
        st.session_state.cart_items.append(
            {
                "Product_name": product["Product_name"],
                "Price": price,
                "Price_with_Tax": price_with_tax,
                "Weight": product["Weight"],
                "Quantity": quantity,
                "Total_price": price * quantity,
                "Total_Price_with_Tax": price_with_tax * quantity,
            }
        )


def remove_item_from_cart(product_name):
    """Removes an item from the shopping cart based on the product name.

    This function checks if the specified product is in the user's cart. If the product is found and its quantity is greater than one, the function decreases the quantity by one and updates the total price and total price with tax. If the quantity is one, the product is removed from the cart entirely. If the product is not found, a warning message is displayed.

    Args:
        product_name (str): The name of the product to be removed from the cart.

    Returns:
        None: This function does not return a value. It modifies the session state directly and triggers a rerun of the Streamlit app.
    """

    existing = next(
        (
            item
            for item in st.session_state.cart_items
            if item["Product_name"] == product_name
        ),
        None,
    )

    if existing:
        if existing["Quantity"] > 1:
            existing["Quantity"] -= 1
            existing["Total_price"] = existing["Quantity"] * existing["Price"]
            existing["Total_Price_with_Tax"] = (
                existing["Quantity"] * existing["Price_with_Tax"]
            )
            # st.session_state.success_message = f"One {product_name} has been removed from your cart."
        else:
            st.session_state.cart_items.remove(existing)
            # st.session_state.success_message = f"{product_name} has been removed from your cart."
        st.rerun()
    else:
        st.warning(f"{product_name} not found in your cart.")


def display_cart_summary():
    """Displays a summary of the shopping cart, including item details and total prices.

    This function iterates through the items in the shopping cart stored in the session state,
    calculating the total base price and total price with tax. It formats the details of each
    item and appends them to a list, which is returned at the end.

    Returns:
        list: A list of strings representing the cart summary, including each item's quantity,
        product name, price, price with tax, and the total prices.
    """

    total_base = 0
    total_with_tax = 0
    lines = []

    for item in st.session_state.cart_items:
        item_total_base = item["Total_price"]
        item_total_with_tax = item["Total_Price_with_Tax"]

        line = (
            f"{item['Quantity']} x {item['Product_name']} \n"
            # f"Price: {item['Price']} 円\n"
            f"Price with Tax: {item['Price_with_Tax']} 円"
        )
        lines.append(line)

        total_base += item_total_base
        total_with_tax += item_total_with_tax

    lines.append("---")
    # lines.append(f"**Total price: {total_base} 円**")
    lines.append(f"**Total price: {total_with_tax} 円(税込)**")
    return lines
