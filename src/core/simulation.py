import os
import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
import uuid

# Initialize Faker with Korean locale
fake = Faker('ko_KR')

# Constants
NUM_USERS = 1000
START_DATE = datetime.now() - timedelta(days=90)  # 3 months ago
END_DATE = datetime.now()
RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'raw_data')

def setup_directories():
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)
        print(f"Created directory: {RAW_DATA_DIR}")

def generate_users(n=NUM_USERS):
    print(f"Generating {n} users...")
    users = []
    for _ in range(n):
        uid = str(uuid.uuid4())
        join_date = fake.date_time_between(start_date=START_DATE, end_date=END_DATE)
        
        # Simple segmentation logic
        age = random.randint(18, 60)
        job = fake.job()
        if 18 <= age <= 26:
            segment = 'Student'
        else:
            segment = 'Office Worker'
            
        users.append({
            'user_id': uid,
            'name': fake.name(),
            'gender': random.choice(['M', 'F']),
            'age': age,
            'job': job,
            'segment': segment,
            'joined_at': join_date
        })
    
    df = pd.DataFrame(users)
    df.to_csv(os.path.join(RAW_DATA_DIR, 'users.csv'), index=False)
    print(f"Saved users.csv with {len(df)} records.")
    return df

def generate_orders(users_df):
    print("Generating orders...")
    orders = []
    
    # Menu items with price range
    menu_items = {
        'Americano': 4500,
        'Latte': 5000,
        'Espresso': 4000,
        'Cappuccino': 5000,
        'Mocha': 5500,
        'Tea': 4500,
        'Sandwich': 7000,
        'Cake': 6500
    }
    menu_list = list(menu_items.keys())
    
    for _, user in users_df.iterrows():
        # Random number of orders per user based on segment maybe?
        # Let's keep it random for now: 0 to 20 orders
        num_orders = random.randint(0, 20)
        
        if num_orders == 0:
            continue
            
        # Orders must be after join date
        user_join_date = user['joined_at']
        
        for _ in range(num_orders):
            order_time = fake.date_time_between(start_date=user_join_date, end_date=END_DATE)
            item = random.choice(menu_list)
            price = menu_items[item]
            
            orders.append({
                'order_id': str(uuid.uuid4()),
                'user_id': user['user_id'],
                'order_at': order_time,
                'menu_item': item,
                'amount': price
            })
            
    df = pd.DataFrame(orders)
    # Sort by time
    df = df.sort_values('order_at')
    df.to_csv(os.path.join(RAW_DATA_DIR, 'orders.csv'), index=False)
    print(f"Saved orders.csv with {len(df)} records.")
    return df

def generate_ab_test_logs(users_df):
    print("Generating A/B test logs...")
    logs = []
    
    # Experiment: Push Notification for Discount
    # Control: No Push
    # Test: Push Sent
    
    # Assign groups randomly 50/50
    user_groups = {}
    for uid in users_df['user_id']:
        user_groups[uid] = random.choice(['control', 'test'])
        
    # Generate logs
    # Events: 'exposure', 'click', 'conversion'
    # Control group sees 'exposure' (maybe just app open?) 
    # Test group sees 'exposure' (push received)
    
    for _, user in users_df.iterrows():
        uid = user['user_id']
        group = user_groups[uid]
        join_date = user['joined_at']
        
        # Simulate interaction time
        interaction_time = fake.date_time_between(start_date=join_date, end_date=END_DATE)
        
        # Log exposure
        logs.append({
             'log_id': str(uuid.uuid4()),
             'user_id': uid,
             'event_time': interaction_time,
             'event_name': 'exposure',
             'group_id': group
        })
        
        # Conversion logic
        # Test group might have higher conversion
        conversion_rate = 0.15 if group == 'test' else 0.10
        
        if random.random() < conversion_rate:
            # Add some delay for conversion
            conversion_time = interaction_time + timedelta(minutes=random.randint(1, 60))
            if conversion_time < END_DATE:
                logs.append({
                    'log_id': str(uuid.uuid4()),
                    'user_id': uid,
                    'event_time': conversion_time,
                    'event_name': 'click',
                    'group_id': group
                })
                
    df = pd.DataFrame(logs)
    df = df.sort_values('event_time')
    df.to_csv(os.path.join(RAW_DATA_DIR, 'ab_test_logs.csv'), index=False)
    print(f"Saved ab_test_logs.csv with {len(df)} records.")
    return df

if __name__ == "__main__":
    setup_directories()
    users_df = generate_users()
    orders_df = generate_orders(users_df)
    ab_df = generate_ab_test_logs(users_df)
    print("Data generation complete.")
