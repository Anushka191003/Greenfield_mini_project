import pandas as pd
from sqlalchemy import create_engine, text
import os

# 1. Connect to MySQL (Change 'your_password' to your actual MySQL password)
# Format: mysql+pymysql://username:password@host:port/database_name
# Replace 'YOUR_NEW_PASSWORD' with your updated Workbench password
engine = create_engine('mysql+pymysql://root:Secure123@localhost:3306/hr_oltp')

# 2. Define your exact Desktop paths
base_path = r"C:\Users\AnushkaA\Desktop\Mini Project\data\synthetic"

files_to_load = {
    'departments': 'departments.csv',
    'employees': 'employees.csv',
    'projects': 'projects.csv',
    'assignments': 'assignments.csv',
    'reviews': 'reviews.csv',
    'employee_history': 'employee_history.csv'
}

print("Starting data ingestion to MySQL...")

# Make reruns deterministic while preserving the schema and foreign keys.
with engine.begin() as connection:
    connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    for table_name in reversed(list(files_to_load)):
        connection.execute(text(f"TRUNCATE TABLE `{table_name}`"))
    connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

# 3. Loop through and push data to MySQL
for table_name, file_name in files_to_load.items():
    file_path = os.path.join(base_path, file_name)
    
    print(f"Loading {file_name} into table '{table_name}'...")
    
    # Read the CSV
    df = pd.read_csv(file_path)
    
    # Push to MySQL in chunks of 5,000 to prevent memory crashes
    df.to_sql(
        name=table_name, 
        con=engine, 
        if_exists='append', # Appends to the tables you already created
        index=False,
        chunksize=5000
    )
    print(f"  -> Successfully loaded {len(df)} rows.")

print("\nAll data successfully loaded into hr_oltp!")