import streamlit as st
import json

from Agent.cart import add_item_to_cart, display_cart_summary
from Agent.product import get_available_ingredients



def product_cart(product_input, language):
    products = get_available_ingredients(product_input, language)
    # print('---------products', products)
    st.session_state.available_ingredients = products
    st.session_state.search_done = True  

    # Show matching products if search was done
    if st.session_state.search_done and not st.session_state.available_ingredients:
        st.warning("⚠️ No matching product found.")
    elif st.session_state.search_done:
        st.subheader("Matching Products:")
        product_list = st.session_state.available_ingredients

        for i, product in enumerate(product_list):
            st.subheader(f"{product['Product_name']}")
            st.write(f"Price with Tax: {product['Tax']}")
            st.write(f"Price: {product['Price']}")
            st.write(f"Weight: {product['Weight']}")

            quantity = st.number_input(
                f"Quantity for {product['Product_name']}",
                min_value=1, max_value=10, value=1, step=1, key=f"qty_{i}"
            )

            if st.button(f"Add to Cart", key=f"add_{i}"):
                # st.write('🛒 Button clicked for:', product["Product_name"])
                add_item_to_cart(product, quantity)
                st.session_state.last_added = product["Product_name"]
                # st.experimental_rerun()  # Force refresh to show cart update immediately

    if st.session_state.last_added:
        st.success(f"✅ {st.session_state.last_added} added to cart!")
        st.session_state.last_added = None

    if st.session_state.cart_items:
        st.title("🧺 Your Cart:")
        for item_line in display_cart_summary():
            st.write(item_line)


def get_product_suggestions(language):  
    st.title("🛒 Product Finder")
    product_input = st.text_input("Enter products or ingredients:")
    if st.button("Find Products"):
        product_cart(product_input.split(","), language)
        # Simulate product search
    #     products = get_available_ingredients(product_input.split(","), language)
    #     # print('---------products', products)
    #     st.session_state.available_ingredients = products
    #     st.session_state.search_done = True  

    # # Show matching products if search was done
    # if st.session_state.search_done and not st.session_state.available_ingredients:
    #     st.warning("⚠️ No matching product found.")
    # elif st.session_state.search_done:
    #     st.subheader("Matching Products:")
    #     product_list = st.session_state.available_ingredients

    #     for i, product in enumerate(product_list):
    #         st.subheader(f"{product['Product_name']}")
    #         st.write(f"Price with Tax: {product['Tax']}")
    #         st.write(f"Price: {product['Price']}")
    #         st.write(f"Weight: {product['Weight']}")

    #         quantity = st.number_input(
    #             f"Quantity for {product['Product_name']}",
    #             min_value=1, max_value=10, value=1, step=1, key=f"qty_{i}"
    #         )

    #         if st.button(f"Add to Cart", key=f"add_{i}"):
    #             # st.write('🛒 Button clicked for:', product["Product_name"])
    #             add_item_to_cart(product, quantity)
    #             st.session_state.last_added = product["Product_name"]
    #             # st.experimental_rerun()  # Force refresh to show cart update immediately

    # if st.session_state.last_added:
    #     st.success(f"✅ {st.session_state.last_added} added to cart!")
    #     st.session_state.last_added = None

    # if st.session_state.cart_items:
    #     st.title("🧺 Your Cart:")
    #     for item_line in display_cart_summary():
    #         st.write(item_line)


