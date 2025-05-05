import streamlit as st
from Agent.cart import add_item_to_cart, display_cart_summary, remove_item_from_cart


def render_matching_products(products: list[dict]):
    """Render a list of matching products for display and interaction.

    This function takes a list of products and displays their details, including name, price, and weight. It also provides an option to select a quantity and add the product to the cart. If no products are found, an error message is displayed.

    Args:
        products (list[dict]): A list of dictionaries, where each dictionary contains details of a product, including 'Product_name', 'Tax', 'Price', and 'Weight'.

    Returns:
        None: This function does not return a value but updates the Streamlit app's state and UI.

    Raises:
        None: This function does not raise any exceptions.

    Example:
        render_matching_products(products)
    """

    if not products:
        st.error("No matching product found")

    st.subheader("Matching Products:")
    for i, product in enumerate(products):
        st.subheader(product["Product_name"])
        st.write(f"Price with Tax: {product['Tax']}")
        st.write(f"Price: {product['Price']}")
        st.write(f"Weight: {product['Weight']}")

        quantity = st.number_input(
            f"Quantity for {product['Product_name']}",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
            key=f"qty_{i}",
        )
        if st.button(f"Add to Cart", key=f"add_{i}"):
            add_item_to_cart(product, quantity)
            st.session_state.last_added = product["Product_name"]

    if st.session_state.last_added:
        st.success(f"✅ {st.session_state.last_added} added to cart!")
        st.session_state.last_added = None


def render_cart():
    """Render the shopping cart interface for the user.

    This function checks if there are items in the user's cart and displays the cart summary.
    It allows the user to select an item from the cart to remove it.

    If the cart is not empty, the function will:
    1. Display the title "Your Cart".
    2. Show a summary of the items in the cart.
    3. Provide a dropdown to select an item to remove.
    4. Include a button to confirm the removal of the selected item.

    Returns:
        None
    """

    if st.session_state.cart_items:
        st.title("🧺 Your Cart:")
        for item_line in display_cart_summary():
            st.write(item_line)

        cart_names = [item["Product_name"] for item in st.session_state.cart_items]
        remove_choice = st.selectbox("Remove item from cart:", cart_names)
        if st.button("Remove selected item"):
            remove_item_from_cart(remove_choice)
