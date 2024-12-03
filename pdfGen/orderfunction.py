import os
import json
from datetime import datetime, timedelta

count_file = "order_count.json"

# Function to load the order count from the JSON file
def load_order_count():
    if os.path.exists(count_file):
        with open(count_file, "r") as f:
            return json.load(f)
    return {}

# Function to save the order count back to the JSON file
def save_order_count(count_data):
    with open(count_file, "w") as f:
        json.dump(count_data, f)

# Function to generate a unique order ID
def generate_order_id():
    # Get today's date in YYYYMMDD format
    today = datetime.today() +  timedelta(days = 3)
    today = today.strftime('%Y%m%d')
    
    # Load the current count of reports for the day
    order_count = load_order_count()
    
    # If today's date is not in the dictionary, initialize it
    if today not in order_count:
        order_count[today] = 0
    
    # Increment the order count for the day
    order_count[today] += 1
    
    # Save the updated count back to the JSON file
    save_order_count(order_count)
    
    # Generate the order ID in the desired format (YYYYMMDD-XXXX)
    order_id = f"{today}-{order_count[today]:04d}"  # Zero-padded to 4 digits
    return order_id

# Example usage
if __name__ == "__main__":
    # Generate an order ID
    order_id = generate_order_id()
    print(f"Generated order ID: {order_id}")