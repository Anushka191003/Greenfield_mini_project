-- 1. Create the Databases
CREATE DATABASE IF NOT EXISTS hr_oltp;
CREATE DATABASE IF NOT EXISTS hr_olap;

USE hr_oltp;

-- 2. Drop existing tables to ensure a clean run
DROP TABLE IF EXISTS employee_history;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

-- 3. Create the Staging/OLTP Tables
CREATE TABLE departments (
    department_id VARCHAR(10) PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL
);

CREATE TABLE employees (
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
    -- We temporarily use VARCHAR for booleans to prevent the CSV text 'True'/'False' from crashing the import
    overtime_eligible VARCHAR(10),
    stock_option_level INT,
    total_working_years INT,
    num_companies_worked INT,
    business_travel VARCHAR(50),
    is_active VARCHAR(10),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE projects (
    project_id VARCHAR(15) PRIMARY KEY,
    department_id VARCHAR(10),
    project_name VARCHAR(150),
    client_name VARCHAR(100),
    start_date DATE,
    end_date DATE NULL,
    status VARCHAR(20),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

CREATE TABLE assignments (
    assignment_id VARCHAR(15) PRIMARY KEY,
    employee_id INT,
    project_id VARCHAR(15),
    assignment_role VARCHAR(50),
    allocation_percentage INT,
    start_date DATE,
    end_date DATE NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE reviews (
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
);

CREATE TABLE employee_history (
    history_id VARCHAR(15) PRIMARY KEY,
    employee_id INT,
    change_date DATE,
    change_type VARCHAR(50),
    old_department_id VARCHAR(10),
    old_job_role VARCHAR(100),
    old_job_level INT,
    old_base_salary INT,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

USE hr_oltp;

SELECT 'departments' AS Table_Name, COUNT(*) AS Row_Count FROM departments
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



-- ==========================================
-- STEP 3: CREATE OLAP DATA WAREHOUSE (STAR SCHEMA)
USE hr_olap;

-- Drop existing tables to ensure a clean run
DROP TABLE IF EXISTS Fact_PerformanceReviews;
DROP TABLE IF EXISTS Dim_Project;
DROP TABLE IF EXISTS Dim_Employee;
DROP TABLE IF EXISTS Dim_Department;
DROP TABLE IF EXISTS Dim_Date;

-- ------------------------------------------
-- DIMENSION TABLES
-- ------------------------------------------
CREATE TABLE Dim_Department (
    department_sk INT AUTO_INCREMENT PRIMARY KEY,
    department_id VARCHAR(10) NOT NULL,
    department_name VARCHAR(100) NOT NULL
);

CREATE TABLE Dim_Employee (
    employee_sk INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    gender VARCHAR(20),
    date_of_birth DATE,
    department_id VARCHAR(10),
    job_role VARCHAR(100),
    job_level INT,
    base_salary INT,
    marital_status VARCHAR(20),
    education_level INT,
    education_field VARCHAR(50),
    hire_date DATE,
    -- SCD Type 2 Tracking Columns
    effective_start_date DATE NOT NULL,
    effective_end_date DATE NULL,
    is_current BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE Dim_Project (
    project_sk INT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(15) NOT NULL,
    project_name VARCHAR(150),
    client_name VARCHAR(100),
    owning_department_id VARCHAR(10),
    start_date DATE,
    end_date DATE NULL,
    status VARCHAR(20)
);

CREATE TABLE Dim_Date (
    date_key INT PRIMARY KEY, -- Stored as YYYYMMDD (e.g., 20231215)
    full_date DATE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    day_of_month INT NOT NULL,
    day_of_week_name VARCHAR(15) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- ------------------------------------------
-- FACT TABLE
-- ------------------------------------------
CREATE TABLE Fact_PerformanceReviews (
    review_fact_id INT AUTO_INCREMENT PRIMARY KEY,
    review_id VARCHAR(15) NOT NULL,
    employee_sk INT NOT NULL,
    department_sk INT NOT NULL,
    review_date_key INT NOT NULL,
    performance_rating INT,
    job_satisfaction INT,
    environment_satisfaction INT,
    relationship_satisfaction INT,
    job_involvement INT,
    work_life_balance INT,
    training_times_last_year INT,
    percent_salary_hike INT,
    
    -- Foreign Keys linking the Fact table to the Dimensions
    FOREIGN KEY (employee_sk) REFERENCES Dim_Employee(employee_sk),
    FOREIGN KEY (department_sk) REFERENCES Dim_Department(department_sk),
    FOREIGN KEY (review_date_key) REFERENCES Dim_Date(date_key)
);
-- ==========================================
-- STEP 1: INITIALIZE OLAP DATABASE
-- ==========================================
CREATE DATABASE IF NOT EXISTS hr_olap;
USE hr_olap;

-- Drop existing tables for a clean slate[cite: 1]
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS Fact_PerformanceReviews;
DROP TABLE IF EXISTS Dim_Project;
DROP TABLE IF EXISTS Dim_Employee;
DROP TABLE IF EXISTS Dim_Department;
DROP TABLE IF EXISTS Dim_Date;
SET FOREIGN_KEY_CHECKS = 1;

-- ==========================================
-- STEP 2: CREATE DIMENSION TABLES
-- ==========================================
CREATE TABLE Dim_Department (
    department_sk INT AUTO_INCREMENT PRIMARY KEY, -- Surrogate Key
    department_id VARCHAR(10) UNIQUE NOT NULL,
    department_name VARCHAR(100) NOT NULL
);

CREATE TABLE Dim_Employee (
    employee_sk INT AUTO_INCREMENT PRIMARY KEY, -- Surrogate Key[cite: 2]
    employee_id INT NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    gender VARCHAR(20),
    date_of_birth DATE,
    department_id VARCHAR(10),
    job_role VARCHAR(100),
    job_level INT,
    base_salary INT,
    marital_status VARCHAR(20),
    education_level INT,
    education_field VARCHAR(50),
    hire_date DATE,
-- SCD Type 2 Tracking Columns
    effective_start_date DATE NOT NULL,
    effective_end_date DATE NULL,
    is_current BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE Dim_Project (
    project_sk INT AUTO_INCREMENT PRIMARY KEY, -- Surrogate Key[cite: 2]
    project_id VARCHAR(15) UNIQUE NOT NULL,
    project_name VARCHAR(150),
    client_name VARCHAR(100),
    owning_department_id VARCHAR(10),
    start_date DATE,
    end_date DATE NULL,
    status VARCHAR(20)
);

CREATE TABLE Dim_Date (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    day_of_month INT NOT NULL,
    day_of_week_name VARCHAR(15) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- ==========================================
-- STEP 3: CREATE FACT TABLE
-- ==========================================
CREATE TABLE Fact_PerformanceReviews (
    review_fact_id INT AUTO_INCREMENT PRIMARY KEY,
    review_id VARCHAR(15) NOT NULL,
    employee_sk INT NOT NULL,
    department_sk INT NOT NULL,
    review_date_key INT NOT NULL,
    performance_rating INT,
    job_satisfaction INT,
    environment_satisfaction INT,
    relationship_satisfaction INT,
    job_involvement INT,
    work_life_balance INT,
    training_times_last_year INT,
    percent_salary_hike INT,

    FOREIGN KEY (employee_sk) REFERENCES Dim_Employee(employee_sk),
    FOREIGN KEY (department_sk) REFERENCES Dim_Department(department_sk),
    FOREIGN KEY (review_date_key) REFERENCES Dim_Date(date_key)
);





DELIMITER //

-- ---------------------------------------------------------
-- Proc 1: Populate Dim_Date[cite: 1]
-- ---------------------------------------------------------
CREATE PROCEDURE ETL_PopulateDimDate(IN start_year INT, IN end_year INT)
BEGIN
    DECLARE current_dt DATE;
    DECLARE end_dt DATE;

    SET current_dt = STR_TO_DATE(CONCAT(start_year, '-01-01'), '%Y-%m-%d');
    SET end_dt = STR_TO_DATE(CONCAT(end_year, '-12-31'), '%Y-%m-%d');

    -- Only populate if empty to save time on daily runs
    IF (SELECT COUNT(*) FROM Dim_Date) = 0 THEN
        WHILE current_dt <= end_dt DO
            INSERT INTO Dim_Date (
                date_key, full_date, year, quarter, month, month_name,
                day_of_month, day_of_week_name, is_weekend
            )
            VALUES (
                CAST(DATE_FORMAT(current_dt, '%Y%m%d') AS UNSIGNED),
                current_dt, YEAR(current_dt), QUARTER(current_dt), MONTH(current_dt),
                MONTHNAME(current_dt), DAYOFMONTH(current_dt), DAYNAME(current_dt),
                IF(WEEKDAY(current_dt) IN (5, 6), TRUE, FALSE)
            );
            SET current_dt = DATE_ADD(current_dt, INTERVAL 1 DAY);
        END WHILE;
    END IF;
END //

-- ---------------------------------------------------------
-- Proc 2: Load Dim_Department & Dim_Project (SCD Type 1)
-- ---------------------------------------------------------
CREATE PROCEDURE ETL_LoadSimpleDimensions()
BEGIN
    -- Upsert logic for Departments
    INSERT INTO Dim_Department (department_id, department_name)
    SELECT department_id, department_name FROM hr_oltp.departments
    ON DUPLICATE KEY UPDATE department_name = VALUES(department_name);

    -- Upsert logic for Projects
    INSERT INTO Dim_Project (project_id, project_name, client_name, owning_department_id, start_date, end_date, status)
    SELECT project_id, project_name, client_name, department_id, start_date, end_date, status
    FROM hr_oltp.projects
    ON DUPLICATE KEY UPDATE
        project_name = VALUES(project_name),
        client_name = VALUES(client_name),
        owning_department_id = VALUES(owning_department_id),
        status = VALUES(status),
        end_date = VALUES(end_date);
END //

-- ---------------------------------------------------------
-- Proc 3: Load Dim_Employee (SCD Type 2 via Window Functions)[cite: 1, 2]
-- ---------------------------------------------------------
CREATE PROCEDURE ETL_LoadDimEmployeeSCD2()
BEGIN
    TRUNCATE TABLE Dim_Employee;

    INSERT INTO Dim_Employee (
        employee_id, first_name, last_name, gender, date_of_birth,
        department_id, job_role, job_level, base_salary, marital_status,
        education_level, education_field, hire_date,
        effective_start_date, effective_end_date, is_current
    )
    WITH EmployeeTimeline AS (
        -- Historical States (Pre-Change)
        SELECT
            e.employee_id, e.first_name, e.last_name, e.gender, e.date_of_birth,
            h.old_department_id AS department_id, h.old_job_role AS job_role,
            h.old_job_level AS job_level, h.old_base_salary AS base_salary,
            e.marital_status, e.education_level, e.education_field, e.hire_date,
            h.change_date AS event_date,
            0 AS is_current_flag
        FROM hr_oltp.employees e
        JOIN hr_oltp.employee_history h ON e.employee_id = h.employee_id

        UNION ALL

        -- Current State
        SELECT
            e.employee_id, e.first_name, e.last_name, e.gender, e.date_of_birth,
            e.department_id, e.job_role, e.job_level, e.base_salary,
            e.marital_status, e.education_level, e.education_field, e.hire_date,
            '9999-12-31' AS event_date,
            1 AS is_current_flag
        FROM hr_oltp.employees e
    ),
    RankedTimeline AS (
        SELECT
            *,
            -- Use Window Function to dynamically calculate start date[cite: 2]
            LAG(event_date, 1, hire_date) OVER (PARTITION BY employee_id ORDER BY event_date) AS effective_start_date,
            -- End date is the day before the next event date
            CASE WHEN is_current_flag = 1 THEN NULL ELSE DATE_SUB(event_date, INTERVAL 1 DAY) END AS effective_end_date
        FROM EmployeeTimeline
    )
    SELECT
        employee_id, first_name, last_name, gender, date_of_birth,
        department_id, job_role, job_level, base_salary, marital_status,
        education_level, education_field, hire_date,
        effective_start_date, effective_end_date,
        IF(is_current_flag = 1, TRUE, FALSE) AS is_current
    FROM RankedTimeline;
END //

-- ---------------------------------------------------------
-- Proc 4: Load Fact_PerformanceReviews[cite: 1]
-- ---------------------------------------------------------
DELIMITER //

DROP PROCEDURE IF EXISTS ETL_LoadFactReviews //

CREATE PROCEDURE ETL_LoadFactReviews()
BEGIN
    TRUNCATE TABLE Fact_PerformanceReviews;

    INSERT INTO Fact_PerformanceReviews (
        review_id, employee_sk, department_sk, review_date_key,
        performance_rating, job_satisfaction, environment_satisfaction,
        relationship_satisfaction, job_involvement, work_life_balance,
        training_times_last_year, percent_salary_hike
    )
    SELECT
        r.review_id,
        e.employee_sk,
        d.department_sk,
        CAST(DATE_FORMAT(r.review_date, '%Y%m%d') AS UNSIGNED) AS review_date_key,
        r.performance_rating, r.job_satisfaction, r.environment_satisfaction,
        r.relationship_satisfaction, r.job_involvement, r.work_life_balance,
        r.training_times_last_year, r.percent_salary_hike
    FROM hr_oltp.reviews r
    -- Bind to correct historical employee record using active date range
    JOIN Dim_Employee e ON r.employee_id = e.employee_id
        AND r.review_date >= e.effective_start_date
        AND (e.effective_end_date IS NULL OR r.review_date <= e.effective_end_date)
    JOIN Dim_Department d ON e.department_id = d.department_id;
END //

-- ---------------------------------------------------------
-- 2. Master Orchestrator Procedure
-- ---------------------------------------------------------
DROP PROCEDURE IF EXISTS ETL_Master_Orchestration //

CREATE PROCEDURE ETL_Master_Orchestration()
BEGIN
    SET FOREIGN_KEY_CHECKS = 0;

    CALL ETL_PopulateDimDate(2010, 2030);
    CALL ETL_LoadSimpleDimensions();
    CALL ETL_LoadDimEmployeeSCD2();
    CALL ETL_LoadFactReviews();

    SET FOREIGN_KEY_CHECKS = 1;
END //

DELIMITER ;

-- ---------------------------------------------------------
-- 3. Daily Event Scheduler Configuration
-- ---------------------------------------------------------
-- Ensure the Event Scheduler is running on the MySQL server
SET GLOBAL event_scheduler = ON;

-- Create the daily automated refresh event
DROP EVENT IF EXISTS Run_Daily_HR_ETL;

CREATE EVENT Run_Daily_HR_ETL
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_DATE + INTERVAL 1 DAY
DO
    CALL hr_olap.ETL_Master_Orchestration();
    
    
USE hr_olap;
CALL ETL_Master_Orchestration();



