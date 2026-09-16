import pandas as pd
from faker import Faker
import numpy as np
import os
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# ==========================================
# PHASE 5: DATA CLEANING (Unchanged)
# ==========================================
df = pd.read_csv("IBM Dataset/WA_Fn-UseC_-HR-Employee-Attrition.csv")

cols_to_drop = [
    'DailyRate', 'HourlyRate', 'MonthlyRate', 'EmployeeCount', 
    'Over18', 'StandardHours', 'YearsWithCurrManager', 
    'YearsInCurrentRole', 'YearsSinceLastPromotion'
]
df_clean = df.drop(columns=cols_to_drop)

df_clean['is_active'] = df_clean['Attrition'].apply(lambda x: False if x == 'Yes' else True)
df_clean['overtime_eligible'] = df_clean['OverTime'].apply(lambda x: True if x == 'Yes' else False)
df_clean = df_clean.drop(columns=['Attrition', 'OverTime'])
df_clean['BusinessTravel'] = df_clean['BusinessTravel'].str.replace('Travel_', '')

ANCHOR_DATE = datetime(2023, 1, 1)
def calc_date(years_ago):
    return (ANCHOR_DATE - relativedelta(years=years_ago)).strftime('%Y-%m-%d')

df_clean['date_of_birth'] = df_clean['Age'].apply(calc_date)
df_clean['hire_date'] = df_clean['YearsAtCompany'].apply(calc_date)
df_clean = df_clean.drop(columns=['Age', 'YearsAtCompany'])

df_clean.columns = [col.lower() for col in df_clean.columns]
df_clean.rename(columns={
    'employeenumber': 'employee_id', 'department': 'department_name', 'distancefromhome': 'distance_from_home', 
    'education': 'education_level', 'educationfield': 'education_field', 'joblevel': 'job_level', 
    'jobrole': 'job_role', 'maritalstatus': 'marital_status', 'monthlyincome': 'base_salary',
    'numcompaniesworked': 'num_companies_worked', 'stockoptionlevel': 'stock_option_level', 
    'totalworkingyears': 'total_working_years', 'businesstravel': 'business_travel',
    'performancerating': 'performance_rating', 'jobsatisfaction': 'job_satisfaction',
    'environmentsatisfaction': 'environment_satisfaction', 'relationshipsatisfaction': 'relationship_satisfaction',
    'jobinvolvement': 'job_involvement', 'worklifebalance': 'work_life_balance',
    'trainingtimeslastyear': 'training_times_last_year', 'percentsalaryhike': 'percent_salary_hike'
}, inplace=True)


# ==========================================
# REVISED PHASE 6: DEPARTMENT AND EMPLOYEE MASTER DATA
# ==========================================
# REVISION: We now explicitly define 7 realistic enterprise departments.
department_mapping = {
    'Sales': 'DPT-001',
    'Research & Development': 'DPT-002',
    'Human Resources': 'DPT-003',
    'Finance': 'DPT-004',
    'Information Technology': 'DPT-005',
    'Marketing': 'DPT-006',
    'Operations': 'DPT-007'
}
df_departments = pd.DataFrame(list(department_mapping.items()), columns=['department_name', 'department_id'])
df_departments = df_departments[['department_id', 'department_name']]

# Map back the base IBM departments to df_clean so we don't break the base rows
df_clean['department_id'] = df_clean['department_name'].map(department_mapping)

review_cols = [
    'performance_rating', 'job_satisfaction', 'environment_satisfaction', 
    'relationship_satisfaction', 'job_involvement', 'work_life_balance', 
    'training_times_last_year', 'percent_salary_hike'
]
df_employees = df_clean.drop(columns=['department_name'] + review_cols)


# ==========================================
# REVISED PHASE 7: SYNTHETIC EMPLOYEE GENERATION
# ==========================================
print("\n--- Generating 25,000 Employees (Across 7 Departments) ---")
fake = Faker()
Faker.seed(42)
np.random.seed(42)

TARGET_EMPLOYEE_COUNT = 25000

# 1. Sample with replacement. 
# REVISION: We rename the old ID to `base_employee_id` so we remember exactly which IBM profile they came from.
df_emp_scaled = df_employees.sample(n=TARGET_EMPLOYEE_COUNT, replace=True, random_state=42).reset_index(drop=True)
df_emp_scaled.rename(columns={'employee_id': 'base_employee_id'}, inplace=True)
df_emp_scaled['employee_id'] = range(1, TARGET_EMPLOYEE_COUNT + 1)

first_names = [fake.first_name() for _ in range(TARGET_EMPLOYEE_COUNT)]
last_names = [fake.last_name() for _ in range(TARGET_EMPLOYEE_COUNT)]
df_emp_scaled.insert(2, 'first_name', first_names)
df_emp_scaled.insert(3, 'last_name', last_names)

# REVISION: Distribute employees realistically across all 7 departments.
new_dept_distribution = np.random.choice(
    ['DPT-001', 'DPT-002', 'DPT-003', 'DPT-004', 'DPT-005', 'DPT-006', 'DPT-007'], 
    size=TARGET_EMPLOYEE_COUNT, 
    p=[0.20, 0.20, 0.05, 0.10, 0.20, 0.10, 0.15] # Weighted for realism (e.g., IT/Sales are bigger than HR)
)
df_emp_scaled['department_id'] = new_dept_distribution

# REVISION: Map job roles intelligently based on the NEW department but the EXISTING job_level.
def map_new_role(row):
    dept = row['department_id']
    level = row['job_level']
    role_map = {
        'DPT-001': {1: 'Sales Representative', 2: 'Sales Executive', 3: 'Senior Sales Exec', 4: 'Sales Manager', 5: 'VP of Sales'},
        'DPT-002': {1: 'Lab Technician', 2: 'Research Scientist', 3: 'Senior Researcher', 4: 'R&D Manager', 5: 'R&D Director'},
        'DPT-003': {1: 'HR Assistant', 2: 'HR Generalist', 3: 'HR Partner', 4: 'HR Manager', 5: 'HR Director'},
        'DPT-004': {1: 'Financial Clerk', 2: 'Financial Analyst', 3: 'Senior Analyst', 4: 'Finance Manager', 5: 'CFO'},
        'DPT-005': {1: 'IT Support', 2: 'Software Engineer', 3: 'Senior Engineer', 4: 'IT Manager', 5: 'CIO'},
        'DPT-006': {1: 'Marketing Coord', 2: 'Marketing Specialist', 3: 'Senior Marketer', 4: 'Marketing Manager', 5: 'CMO'},
        'DPT-007': {1: 'Operations Asst', 2: 'Operations Analyst', 3: 'Senior Analyst', 4: 'Operations Manager', 5: 'COO'}
    }
    return role_map.get(dept, {}).get(level, 'Specialist')

df_emp_scaled['job_role'] = df_emp_scaled.apply(map_new_role, axis=1)

variance = np.random.uniform(0.95, 1.05, TARGET_EMPLOYEE_COUNT)
df_emp_scaled['base_salary'] = (df_emp_scaled['base_salary'] * variance).astype(int)

# We temporarily keep base_employee_id for Phase 10
working_emp_columns = [
    'employee_id', 'base_employee_id', 'department_id', 'first_name', 'last_name', 'gender', 
    'date_of_birth', 'marital_status', 'distance_from_home', 'education_level', 
    'education_field', 'hire_date', 'job_role', 'job_level', 'base_salary', 
    'overtime_eligible', 'stock_option_level', 'total_working_years', 
    'num_companies_worked', 'business_travel', 'is_active'
]
df_emp_scaled = df_emp_scaled[working_emp_columns]

print(f"Total Employees Generated: {len(df_emp_scaled)}")
print("\nSample of Final Employee Data (Showing Dynamic Roles):")
print(df_emp_scaled[['employee_id', 'department_id', 'job_level', 'job_role', 'base_salary']].head(5).to_string())


# ==========================================
# PHASE 8: PROJECT DATA GENERATION (Unchanged Logic, Adapts Automatically)
# ==========================================
print("\n--- Generating 2,500 Projects ---")
TARGET_PROJECT_COUNT = 2500
project_data = []
dept_ids = df_departments['department_id'].tolist()

start_boundary = date(2018, 1, 1)
end_boundary = date(2023, 1, 1)
current_boundary = date(2023, 12, 31)

for i in range(1, TARGET_PROJECT_COUNT + 1):
    p_id = f"PRJ-{i:04d}"
    d_id = np.random.choice(dept_ids)
    p_name = fake.catch_phrase()
    c_name = fake.company()
    
    p_start_date = fake.date_between(start_date=start_boundary, end_date=end_boundary)
    status = np.random.choice(['Active', 'Completed', 'On Hold'], p=[0.6, 0.3, 0.1])
    
    if status == 'Completed':
        p_end_date = fake.date_between(start_date=p_start_date, end_date=current_boundary)
    else:
        p_end_date = None
        
    project_data.append({
        'project_id': p_id, 'department_id': d_id, 'project_name': p_name,
        'client_name': c_name, 'start_date': p_start_date, 'end_date': p_end_date, 'status': status
    })
df_projects = pd.DataFrame(project_data)


# ==========================================
# PHASE 9: ASSIGNMENT DATA GENERATION (Unchanged Logic, Adapts Automatically)
# ==========================================
print("\n--- Generating 40,000 Assignments ---")
TARGET_ASSIGNMENT_COUNT = 40000
emp_sample = df_emp_scaled[['employee_id', 'hire_date']].sample(n=TARGET_ASSIGNMENT_COUNT, replace=True, random_state=42).reset_index(drop=True)
proj_sample = df_projects[['project_id', 'start_date', 'end_date', 'status']].sample(n=TARGET_ASSIGNMENT_COUNT, replace=True, random_state=42).reset_index(drop=True)

df_assign = pd.concat([emp_sample, proj_sample], axis=1)
df_assign['hire_date_dt'] = pd.to_datetime(df_assign['hire_date'])
df_assign['proj_start_dt'] = pd.to_datetime(df_assign['start_date'])
df_assign['proj_end_dt'] = pd.to_datetime(df_assign['end_date'])

df_assign['base_start'] = df_assign[['hire_date_dt', 'proj_start_dt']].max(axis=1)
df_assign['assign_start_dt'] = df_assign['base_start'] + pd.to_timedelta(np.random.randint(0, 15, size=TARGET_ASSIGNMENT_COUNT), unit='D')

mask_exceeds = (df_assign['status'] == 'Completed') & (df_assign['assign_start_dt'] > df_assign['proj_end_dt'])
df_assign.loc[mask_exceeds, 'assign_start_dt'] = df_assign.loc[mask_exceeds, 'proj_start_dt']

def calc_assign_end(row):
    if row['status'] == 'Completed':
        return row['proj_end_dt']
    else:
        if np.random.rand() > 0.85: return row['assign_start_dt'] + pd.Timedelta(days=np.random.randint(30, 180))
        return pd.NaT

df_assign['assign_end_dt'] = df_assign.apply(calc_assign_end, axis=1)
df_assign['start_date'] = df_assign['assign_start_dt'].dt.strftime('%Y-%m-%d')
df_assign['end_date'] = df_assign['assign_end_dt'].dt.strftime('%Y-%m-%d').replace('NaT', None)

df_assign['assignment_id'] = [f"ASN-{i:05d}" for i in range(1, TARGET_ASSIGNMENT_COUNT + 1)]
df_assign['assignment_role'] = np.random.choice(['Lead', 'Contributor', 'Reviewer', 'Consultant'], size=TARGET_ASSIGNMENT_COUNT, p=[0.1, 0.6, 0.2, 0.1])
df_assign['allocation_percentage'] = np.random.choice([25, 50, 75, 100], size=TARGET_ASSIGNMENT_COUNT, p=[0.2, 0.3, 0.1, 0.4])

df_assignments = df_assign[['assignment_id', 'employee_id', 'project_id', 'assignment_role', 'allocation_percentage', 'start_date', 'end_date']]


# ==========================================
# REVISED PHASE 10: PERFORMANCE REVIEW DATA
# ==========================================
print("\n--- Generating Multi-Year Performance Reviews ---")

# REVISION: Directly join on `base_employee_id` to reliably retrieve the original IBM review metrics.
base_reviews = df_clean[['employee_id', 'performance_rating', 'job_satisfaction', 'environment_satisfaction', 
                         'relationship_satisfaction', 'job_involvement', 'work_life_balance', 
                         'training_times_last_year', 'percent_salary_hike']]

emp_review_baseline = pd.merge(
    df_emp_scaled[['employee_id', 'base_employee_id', 'hire_date']], 
    base_reviews, 
    left_on='base_employee_id', 
    right_on='employee_id',
    how='left',
    suffixes=('', '_base')
)

review_data = []
CURRENT_YEAR = 2023

def drift(val, min_v=1, max_v=5):
    return int(max(min_v, min(max_v, val + np.random.choice([-1, 0, 1], p=[0.2, 0.6, 0.2]))))

for emp in emp_review_baseline.to_dict('records'):
    emp_id = emp['employee_id']
    hire_year = int(emp['hire_date'][:4])
    start_review_year = max(hire_year + 1, CURRENT_YEAR) if hire_year == CURRENT_YEAR else hire_year + 1
    
    for review_year in range(start_review_year, CURRENT_YEAR + 1):
        review_date = f"{review_year}-12-{np.random.randint(1, 28):02d}"
        
        review_data.append({
            'employee_id': emp_id,
            'review_date': review_date,
            'performance_rating': drift(emp['performance_rating'], max_v=5),
            'job_satisfaction': drift(emp['job_satisfaction']),
            'environment_satisfaction': drift(emp['environment_satisfaction']),
            'relationship_satisfaction': drift(emp['relationship_satisfaction']),
            'job_involvement': drift(emp['job_involvement'], max_v=4),
            'work_life_balance': drift(emp['work_life_balance'], max_v=4),
            'training_times_last_year': int(max(0, min(6, emp['training_times_last_year'] + np.random.choice([-1,0,1])))),
            'percent_salary_hike': int(max(11, min(25, emp['percent_salary_hike'] + np.random.choice([-2,0,2]))))
        })

df_reviews = pd.DataFrame(review_data)
df_reviews.insert(0, 'review_id', [f"REV-{i:06d}" for i in range(1, len(df_reviews) + 1)])


# ==========================================
# PHASE 11: HISTORICAL DATA FOR SCD TYPE 2
# ==========================================
print("\n--- Generating Historical Records (SCD Type 2 Source) ---")

# Clean up employee table (Drop base_employee_id as it was only needed for generation)
df_emp_scaled = df_emp_scaled.drop(columns=['base_employee_id'])

df_emp_scaled['hire_date_dt'] = pd.to_datetime(df_emp_scaled['hire_date'])
eligible_emps = df_emp_scaled[df_emp_scaled['hire_date_dt'] < pd.to_datetime('2022-01-01')]

history_sample = eligible_emps.sample(frac=0.15, random_state=42).copy()
history_data = []

for idx, row in history_sample.iterrows():
    emp_id = row['employee_id']
    current_dept = row['department_id']
    current_role = row['job_role']
    current_level = row['job_level']
    current_salary = row['base_salary']
    hire_date = row['hire_date_dt']
    
    days_worked = (pd.to_datetime('2023-01-01') - hire_date).days
    if days_worked > 30:
        change_date = (hire_date + pd.Timedelta(days=np.random.randint(30, max(31, days_worked - 15)))).strftime('%Y-%m-%d')
    else:
        change_date = hire_date.strftime('%Y-%m-%d')
    
    event = np.random.choice(['Department Transfer', 'Promotion', 'Merit Increase'], p=[0.3, 0.3, 0.4])
    old_dept = current_dept; old_role = current_role; old_level = current_level; old_salary = current_salary
    
    if event == 'Department Transfer':
        old_dept = np.random.choice([d for d in dept_ids if d != current_dept])
    elif event == 'Promotion':
        old_level = max(1, current_level - 1)
        old_salary = int(current_salary * 0.85)
    elif event == 'Merit Increase':
        old_salary = int(current_salary * 0.92)
        
    history_data.append({
        'employee_id': emp_id, 'change_date': change_date, 'change_type': event,
        'old_department_id': old_dept, 'old_job_role': old_role, 'old_job_level': old_level, 'old_base_salary': old_salary
    })

df_history = pd.DataFrame(history_data)
df_history.insert(0, 'history_id', [f"HIS-{i:05d}" for i in range(1, len(df_history) + 1)])
df_emp_scaled = df_emp_scaled.drop(columns=['hire_date_dt'])

print(f"Total Historical Records Generated: {len(df_history)}")
print(f"GRAND TOTAL RECORDS GENERATED: {len(df_departments) + len(df_emp_scaled) + len(df_projects) + len(df_assignments) + len(df_reviews) + len(df_history)}")

# ==========================================
# PHASE 12: EXPORTING FINAL DATASETS
# ==========================================


print("\n--- Exporting Final Datasets to CSV ---")

# 1. Define the directory structure
base_dir = "data"
raw_dir = os.path.join(base_dir, "raw")
cleaned_dir = os.path.join(base_dir, "cleaned")
synthetic_dir = os.path.join(base_dir, "synthetic")

# Create directories if they don't exist
os.makedirs(raw_dir, exist_ok=True)
os.makedirs(cleaned_dir, exist_ok=True)
os.makedirs(synthetic_dir, exist_ok=True)

# 2. Export the Raw/Cleaned baseline data
df.to_csv(os.path.join(raw_dir, "ibm_hr_raw.csv"), index=False)
df_clean.to_csv(os.path.join(cleaned_dir, "ibm_hr_cleaned_baseline.csv"), index=False)

# 3. Export the Final Synthetic/Master Entities
df_departments.to_csv(os.path.join(synthetic_dir, "departments.csv"), index=False)
df_emp_scaled.to_csv(os.path.join(synthetic_dir, "employees.csv"), index=False)
df_projects.to_csv(os.path.join(synthetic_dir, "projects.csv"), index=False)
df_assignments.to_csv(os.path.join(synthetic_dir, "assignments.csv"), index=False)
df_reviews.to_csv(os.path.join(synthetic_dir, "reviews.csv"), index=False)
df_history.to_csv(os.path.join(synthetic_dir, "employee_history.csv"), index=False)

print(f"Success! All files have been exported to the '{base_dir}' folder in your current directory.")
print("Folder Structure Created:")
print("data/")
print("  ├── raw/ (1 file)")
print("  ├── cleaned/ (1 file)")
print("  └── synthetic/ (6 files)")