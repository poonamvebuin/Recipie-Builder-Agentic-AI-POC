
def get_available_ingredients():
    return [
        {"product_name": "Soy sauce", "description": "condiment", "category": "Condiment", "brand": "Kikkoman", "price": 150.00, "weight": "500ml"},
        {"product_name": "Cucumber", "description": "vegetable", "category": "Vegetable", "brand": "Local Farm", "price": 20.00, "weight": "300g"},
        {"product_name": "Nori", "description": "seaweed", "category": "Seaweed", "brand": "Yamamotoyama", "price": 50.00, "weight": "50g"},
        {"product_name": "Avocado", "description": "avocado", "category": "Fruit", "brand": "Hass", "price": 50.00, "weight": "250g"},
        {"product_name": "Rice", "description": "basmati", "category": "Grain", "brand": "IndiaGate", "price": 100.00, "weight": "1000g"},
        {"product_name": "Tempura shrimp", "description": "shrimp", "category": "Seafood", "brand": "SeaGold", "price": 200.00, "weight": "400g"}
    ]


cart_items = []

def add_item_to_cart(product, quantity):
    cart_items.append({
        "product_name": product["product_name"],
        "description": product["description"],
        "category": product["category"],
        "brand": product["brand"],
        "price": product["price"],
        "weight": product["weight"],
        "quantity": quantity,
        "total_price": product["price"] * quantity
    })

def display_cart_summary():
    total_price = 0
    cart_summary = []

    for item in cart_items:
        cart_summary.append(f"{item['quantity']} x {item['product_name']} ({item['brand']}) - {item['total_price']} Rs")
        total_price += item['total_price']

    cart_summary.append(f"Total: {total_price} Rs")
    return cart_summary


products = get_available_ingredients()

for product in products:
    add_item_to_cart(product, 1) 

print("\nCart Summary:")
cart_summary = display_cart_summary()
for line in cart_summary:
    print(line)
