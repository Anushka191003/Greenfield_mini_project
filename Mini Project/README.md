# People Analytics

Northstar People Analytics is a small HR data platform and Streamlit portal. It manages employee records, projects, assignments, performance reviews, employee history, and analytics.

The project uses:

- Python and pandas for data cleaning and synthetic data generation
- MySQL for OLTP and OLAP databases
- SQL procedures for ETL and SCD Type 2 employee history
- Streamlit for the web portal
- Plotly for charts

## What the Project Does

The system has two database layers:

### OLTP: `hr_oltp`

This is the operational database. It stores:

- Departments
- Employees
- Projects
- Project assignments
- Performance reviews
- Employee history records

### OLAP: `hr_olap`

This is the reporting database. It contains a star schema:

- `Dim_Employee` - employee dimension with SCD Type 2 fields
- `Dim_Department` - department dimension
- `Dim_Project` - project dimension
- `Dim_Date` - calendar dimension
- `Fact_PerformanceReviews` - performance review fact table

## Main Features

The Streamlit portal provides:

- Employee onboarding
- Employee directory search and department filtering
- Employee detail updates
- Employee history lookup
- Project creation
- Employee assignment to projects
- Performance review submission
- Performance review browsing
- Analytics dashboard
- Attrition risk view
- Project pressure view
- Performance leaderboard
- Year-over-year review trends

## Project Structure

```text
Mini Project/
|
|-- app.py                         Streamlit application
|-- Data Cleaning.py               Cleans source data and generates CSV files
|-- load.py                        Loads synthetic CSV files into MySQL OLTP
|-- Sqlscript.sql                  Creates schemas, tables, ETL procedures, and event
|
|-- backend/
|   |-- dal.py                     Database operations and analytics queries
|   |-- db_manager.py              MySQL connection manager
|   |-- models.py                  Simple Python data models
|
|-- data/
|   |-- raw/                       Raw source CSV files
|   |-- cleaned/                   Cleaned baseline CSV files
|   |-- synthetic/                Generated departments, employees, projects, reviews, and history
```

## Requirements

Install these Python packages:

```bash
py -3 -m pip install pandas numpy faker python-dateutil streamlit plotly pymysql sqlalchemy
```

You also need:

- Python 3
- MySQL Server
- MySQL Workbench, recommended for running `Sqlscript.sql`

## Database Configuration

The current database settings are stored in:

- `app.py`
- `load.py`

Update the host, username, password, and database values if your MySQL setup is different. Do not commit real passwords to a public repository.

The default project configuration expects:

```text
Host: localhost
User: root
Password: Secure123
Database: hr_oltp
Port: 3306
```

Change this password before using the project outside your local computer.

## Setup and Run Order

Run the steps in this order when setting up the project for the first time.

### 1. Prepare the source HR dataset

`Data Cleaning.py` expects the original IBM HR CSV at:

```text
IBM Dataset/WA_Fn-UseC_-HR-Employee-Attrition.csv
```

Create that folder and place the source file there, or update the input path in `Data Cleaning.py`.

### 2. Generate the project data

From the project root, run:

```bash
py -3 "Data Cleaning.py"
```

This creates or refreshes files under:

```text
data/raw/
data/cleaned/
data/synthetic/
```

The generated synthetic data includes approximately:

- 25,000 employees
- 2,500 projects
- 40,000 assignments
- Multi-year performance reviews
- Employee history records

### 3. Create the MySQL databases and tables

Open `Sqlscript.sql` in MySQL Workbench and run the script.

The script creates:

- `hr_oltp`
- `hr_olap`
- OLTP tables
- OLAP dimension and fact tables
- ETL stored procedures
- A daily ETL event

### 4. Load the CSV data into OLTP

Run:

```bash
py -3 load.py
```

This loads the files from `data/synthetic/` into `hr_oltp`.

Important: `load.py` truncates the OLTP tables before loading. Use it for a fresh data load, not as a normal daily application command, because it can remove records created through the portal.

### 5. Run the OLAP ETL

In MySQL Workbench, run:

```sql
USE hr_olap;
CALL ETL_Master_Orchestration();
```

This refreshes the reporting dimensions and performance fact table.

### 6. Start the Streamlit portal

From the project root, run:

```bash
py -3 -m streamlit run app.py
```

Then open the local URL shown in the terminal. It is usually:

```text
http://localhost:8501
```

If that port is busy, Streamlit will select another available port.

## Employee History and SCD Type 2

When an employee is updated through the portal:

1. The current employee values are read from `hr_oltp.employees`.
2. The old department, designation, job level, and salary are inserted into `hr_oltp.employee_history`.
3. The employee record is updated.
4. Both actions are committed in one transaction.

The `Employee History` tab lets users enter an employee ID and view previous states.

The OLAP employee dimension uses these SCD Type 2 fields:

- `effective_start_date`
- `effective_end_date`
- `is_current`

The OLAP history becomes current after running:

```sql
CALL ETL_Master_Orchestration();
```

The Streamlit update writes to OLTP immediately. The OLAP warehouse is refreshed separately by the ETL procedure or the MySQL daily event.

## Using the Portal

### Onboard Employee

Use this area to:

- Create a new employee
- Search the employee directory
- Filter employees by department
- Update department, designation, salary, and active status
- View the employee's previous history

### Projects

Use this area to:

- Create a project
- Assign an employee to a project
- View projects

### Performance Review

Use this area to:

- Submit a review
- View review history

### Analytics Dashboard

The dashboard uses OLAP data when available. If the OLAP query returns no data, it falls back to the generated CSV files.

## Useful Database Checks

Check row counts in OLTP:

```sql
USE hr_oltp;

SELECT 'departments' AS table_name, COUNT(*) AS row_count FROM departments
UNION ALL
SELECT 'employees', COUNT(*) FROM employees
UNION ALL
SELECT 'projects', COUNT(*) FROM projects
UNION ALL
SELECT 'assignments', COUNT(*) FROM assignments
UNION ALL
SELECT 'reviews', COUNT(*) FROM reviews
UNION ALL
SELECT 'employee_history', COUNT(*) FROM employee_history;
```

Check an employee's recorded history:

```sql
SELECT *
FROM hr_oltp.employee_history
WHERE employee_id = 1
ORDER BY change_date DESC;
```

Check SCD2 records in OLAP:

```sql
SELECT employee_id, department_id, job_role, base_salary,
       effective_start_date, effective_end_date, is_current
FROM hr_olap.Dim_Employee
WHERE employee_id = 1
ORDER BY effective_start_date;
```

Check the current employee version:

```sql
SELECT *
FROM hr_olap.Dim_Employee
WHERE employee_id = 1
  AND is_current = TRUE;
```

## Common Problems

### Duplicate employee ID

The application calculates the next employee ID from the current maximum database ID. Make sure the MySQL database is reachable and that the latest version of `backend/dal.py` is being used.

### Employee history is empty

Check that:

1. The employee has actually been updated.
2. The update succeeded in the portal.
3. You are checking the correct employee ID.
4. The employee history table contains records.

### Analytics are empty

Run:

```sql
USE hr_olap;
CALL ETL_Master_Orchestration();
```

Also confirm that `Dim_Employee`, `Dim_Department`, `Dim_Date`, and `Fact_PerformanceReviews` contain rows.

### MySQL connection error

Check:

- MySQL Server is running.
- The username and password are correct.
- Port `3306` is available.
- The `hr_oltp` database exists.
- `pymysql` and `sqlalchemy` are installed.

### Data Cleaning script cannot find the source file

Place the IBM HR dataset at:

```text
IBM Dataset/WA_Fn-UseC_-HR-Employee-Attrition.csv
```

or update the path near the top of `Data Cleaning.py`.

## Recommended Development Practice

For a normal development session:

1. Start MySQL.
2. Start the Streamlit app.
3. Use the portal for employee, project, and review changes.
4. Run the OLAP ETL after OLTP changes when analytics need to be refreshed.
5. Avoid running `load.py` unless you intentionally want to reload the complete seed dataset.

## License and Data Note

This project is intended for learning and demonstration. Make sure you have permission to use any external HR dataset included in the project or used during setup.
