import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os
from urllib.parse import urlsplit, urlunsplit

load_dotenv()

# 1. Connect to MySQL using the service URI in .env.
service_url = urlsplit(os.environ["DATABASE_URL"])
database_url = urlunsplit(("mysql+pymysql", service_url.netloc, service_url.path, "", ""))
engine = create_engine(database_url, connect_args={"ssl": {"check_hostname": False}})

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

table_definitions = {
    "departments": """
        CREATE TABLE IF NOT EXISTS departments (
            department_id VARCHAR(10) PRIMARY KEY,
            department_name VARCHAR(100) NOT NULL
        )
    """,
    "employees": """
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INT PRIMARY KEY,
            department_id VARCHAR(10),
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            gender VARCHAR(20),
            date_of_birth DATE,
            marital_status VARCHAR(20),
            distance_from_home INT,
            education_level INT,
            education_field VARCHAR(50),
            hire_date DATE,
            job_role VARCHAR(100),
            job_level INT,
            base_salary INT,
            overtime_eligible VARCHAR(10),
            stock_option_level INT,
            total_working_years INT,
            num_companies_worked INT,
            business_travel VARCHAR(50),
            is_active VARCHAR(10),
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        )
    """,
    "projects": """
        CREATE TABLE IF NOT EXISTS projects (
            project_id VARCHAR(15) PRIMARY KEY,
            department_id VARCHAR(10),
            project_name VARCHAR(150),
            client_name VARCHAR(100),
            start_date DATE,
            end_date DATE NULL,
            status VARCHAR(20),
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        )
    """,
    "assignments": """
        CREATE TABLE IF NOT EXISTS assignments (
            assignment_id VARCHAR(15) PRIMARY KEY,
            employee_id INT,
            project_id VARCHAR(15),
            assignment_role VARCHAR(50),
            allocation_percentage INT,
            start_date DATE,
            end_date DATE NULL,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        )
    """,
    "reviews": """
        CREATE TABLE IF NOT EXISTS reviews (
            review_id VARCHAR(15) PRIMARY KEY,
            employee_id INT,
            review_date DATE,
            performance_rating INT,
            job_satisfaction INT,
            environment_satisfaction INT,
            relationship_satisfaction INT,
            job_involvement INT,
            work_life_balance INT,
            training_times_last_year INT,
            percent_salary_hike INT,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        )
    """,
    "employee_history": """
        CREATE TABLE IF NOT EXISTS employee_history (
            history_id VARCHAR(15) PRIMARY KEY,
            employee_id INT,
            change_date DATE,
            change_type VARCHAR(50),
            old_department_id VARCHAR(10),
            old_job_role VARCHAR(100),
            old_job_level INT,
            old_base_salary INT,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        )
    """,
}

print("Starting data ingestion to MySQL...")

# Make reruns deterministic while preserving the schema and foreign keys.
with engine.begin() as connection:
    for table_name in files_to_load:
        connection.execute(text(table_definitions[table_name]))
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

print("\nAll OLTP data successfully loaded into hr_oltp!")

# Refresh the reporting dimensions and fact table from the newly loaded OLTP data.
with engine.begin() as connection:
    connection.execute(text("CALL hr_olap.ETL_Master_Orchestration()"))

print("OLAP data successfully synchronized into hr_olap!")