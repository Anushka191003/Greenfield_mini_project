from datetime import date, datetime

from backend.db_manager import DatabaseConnection
from backend.models import Employee


class EmployeeManager:
    def __init__(self, db_config):
        # Utilize the Singleton connection
        self.db = DatabaseConnection()
        self.db_config = db_config
        self.last_error = ""

    def get_connection(self):
        return self.db.connect(**self.db_config)

    def get_next_employee_id(self):
        """Fetch the next employee ID from the database."""
        conn = self.get_connection()
        next_id = 25000
        
        if conn:
            cursor = None
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT MAX(employee_id) AS max_id "
                    "FROM employees;"
                )
                row = cursor.fetchone()
                max_id = row.get("max_id") if isinstance(row, dict) else row[0]
                if max_id is not None:
                    next_id = int(max_id)
            except Exception as error:
                self.last_error = f"Failed to determine the next employee ID: {error}"
            finally:
                if cursor:
                    cursor.close()
                    
        return next_id + 1

    def get_employees(self):
        """Return employees from the configured database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT employee_id, department_id, first_name, last_name, gender,
                       date_of_birth, marital_status, distance_from_home,
                       education_level, education_field, hire_date, job_role,
                       job_level, base_salary, overtime_eligible, stock_option_level,
                       total_working_years, num_companies_worked, business_travel,
                       is_active
                FROM employees
                ORDER BY employee_id
                """
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    def get_employee_history(self, employee_id):
        """Return the recorded previous states for an employee."""
        try:
            conn = self.get_connection()
        except Exception as error:
            self.last_error = f"Failed to connect while loading employee history: {error}"
            return []
        if not conn:
            self.last_error = "Database connection failed."
            return []

        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    h.history_id,
                    h.employee_id,
                    h.change_date,
                    h.change_type,
                    h.old_department_id,
                    COALESCE(d.department_name, h.old_department_id) AS old_department_name,
                    h.old_job_role,
                    h.old_job_level,
                    h.old_base_salary
                FROM employee_history h
                LEFT JOIN departments d
                    ON d.department_id = h.old_department_id
                WHERE h.employee_id = %s
                ORDER BY h.change_date DESC, h.history_id DESC
                """,
                (employee_id,),
            )
            self.last_error = ""
            return cursor.fetchall()
        except Exception as error:
            self.last_error = f"Failed to load employee history: {error}"
            return []
        finally:
            if cursor:
                cursor.close()

    def add_employee(self, employee: Employee):
        """Insert a complete employee record into the configured database."""
        # Always fetch fresh next ID directly at insertion time
        new_pk = self.get_next_employee_id()
        employee.employee_id = new_pk

        query = """
            INSERT INTO employees (
                employee_id, department_id, first_name, last_name, gender,
                date_of_birth, marital_status, distance_from_home, education_level,
                education_field, hire_date, job_role, job_level, base_salary,
                overtime_eligible, stock_option_level, total_working_years,
                num_companies_worked, business_travel, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            employee.employee_id,
            employee.department_id,
            employee.first_name,
            employee.last_name,
            getattr(employee, "gender", None),
            getattr(employee, "date_of_birth", None),
            getattr(employee, "marital_status", None),
            getattr(employee, "distance_from_home", None),
            getattr(employee, "education_level", None),
            getattr(employee, "education_field", None),
            getattr(employee, "hire_date", None),
            employee.job_role,
            getattr(employee, "job_level", None),
            employee.base_salary,
            getattr(employee, "overtime_eligible", None),
            getattr(employee, "stock_option_level", None),
            getattr(employee, "total_working_years", None),
            getattr(employee, "num_companies_worked", None),
            getattr(employee, "business_travel", None),
            getattr(employee, "is_active", "True"),
        )
        return self._write(query, values, "add employee")

    def update_employee_details(self, employee_id, new_department_id=None, new_job_role=None, new_salary=None, is_active=True):
        """Unified method: Updates department, job role, salary, and active status in hr_oltp while preserving audit history."""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            # FIX: Use standard cursor without passing invalid dictionary argument
            cursor = conn.cursor()
            
            # Fetch existing state for audit logging
            cursor.execute(
                "SELECT department_id, job_role, job_level, base_salary FROM employees WHERE employee_id = %s FOR UPDATE",
                (employee_id,),
            )
            current = cursor.fetchone()
            if not current:
                self.last_error = f"Employee ID {employee_id} was not found."
                return False

            # Extract tuple values safely (0: dept, 1: role, 2: level, 3: salary)
            old_dept_id = current[0] if isinstance(current, tuple) else current.get("department_id")
            old_job_role = current[1] if isinstance(current, tuple) else current.get("job_role")
            old_job_level = current[2] if isinstance(current, tuple) else current.get("job_level")
            old_base_salary = current[3] if isinstance(current, tuple) else current.get("base_salary")

            change_date = date.today()
            history_id = f"HIS-{int(datetime.now().timestamp())}"[:15]
            
            # Record audit trail in employee_history
            cursor.execute(
                """
                INSERT INTO employee_history (
                    history_id, employee_id, change_date, change_type, old_department_id,
                    old_job_role, old_job_level, old_base_salary
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    history_id,
                    employee_id,
                    change_date,
                    "Consolidated Update",
                    old_dept_id,
                    old_job_role,
                    old_job_level,
                    old_base_salary
                ),
            )

            # Build dynamic UPDATE query
            update_fields = []
            params = []

            if new_department_id:
                update_fields.append("department_id = %s")
                params.append(new_department_id)
            if new_job_role:
                update_fields.append("job_role = %s")
                params.append(new_job_role)
            if new_salary is not None:
                update_fields.append("base_salary = %s")
                params.append(new_salary)
            
            update_fields.append("is_active = %s")
            params.append(is_active)

            params.append(employee_id)

            sql = f"UPDATE employees SET {', '.join(update_fields)} WHERE employee_id = %s"
            cursor.execute(sql, tuple(params))

            conn.commit()
            self.last_error = ""
            return True
        except Exception as error:
            if conn:
                conn.rollback()
            self.last_error = f"Failed to update employee details: {error}"
            print(self.last_error)
            return False
        finally:
            if cursor:
                cursor.close()

    def update_employee_department(self, employee_id, new_department_id, effective_date=None):
        """Update an employee department and preserve previous state."""
        return self._update_with_history(employee_id, new_department_id=new_department_id, effective_date=effective_date, change_type="Department Transfer")

    def update_employee_salary(self, employee_id, new_salary):
        """Update an employee salary and preserve previous state."""
        return self._update_with_history(employee_id, new_salary=new_salary, effective_date=date.today(), change_type="Merit Increase")

    def create_project(self, project_id, department_id, project_name, client_name, start_date, end_date, status):
        query = """
            INSERT INTO projects (project_id, department_id, project_name, client_name, start_date, end_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (project_id, department_id, project_name, client_name, start_date, end_date, status)
        return self._write(query, values, "create project")

    def create_assignment(self, assignment_id, employee_id, project_id, role, allocation, start_date, end_date):
        query = """
            INSERT INTO assignments (assignment_id, employee_id, project_id, assignment_role, allocation_percentage, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (assignment_id, employee_id, project_id, role, allocation, start_date, end_date)
        return self._write(query, values, "assign employee")

    def create_review(self, review_id, employee_id, review_date, performance, job, environment, relationship, involvement, work_life, training, salary_hike):
        query = """
            INSERT INTO reviews (
                review_id, employee_id, review_date, performance_rating, job_satisfaction,
                environment_satisfaction, relationship_satisfaction, job_involvement,
                work_life_balance, training_times_last_year, percent_salary_hike
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (review_id, employee_id, review_date, performance, job, environment, relationship, involvement, work_life, training, salary_hike)
        return self._write(query, values, "submit review")

    def _write(self, query, values, operation):
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            self.last_error = ""
            return True
        except Exception as error:
            if conn:
                conn.rollback()
            self.last_error = f"Failed to {operation}: {error}"
            print(self.last_error)
            return False
        finally:
            if cursor:
                cursor.close()

    def _update_with_history(self, employee_id, new_department_id=None, new_salary=None, effective_date=None, change_type="Update"):
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT department_id, job_role, job_level, base_salary FROM employees WHERE employee_id = %s FOR UPDATE",
                (employee_id,),
            )
            current = cursor.fetchone()
            if not current:
                raise ValueError(f"Employee {employee_id} was not found")
            change_date = effective_date or date.today()
            history_id = f"HIS-{int(datetime.now().timestamp())}"[:15]
            cursor.execute(
                """
                INSERT INTO employee_history (
                    history_id, employee_id, change_date, change_type, old_department_id,
                    old_job_role, old_job_level, old_base_salary
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (history_id, employee_id, change_date, change_type, current["department_id"], current["job_role"], current["job_level"], current["base_salary"]),
            )
            if new_department_id is not None:
                cursor.execute("UPDATE employees SET department_id = %s WHERE employee_id = %s", (new_department_id, employee_id))
            if new_salary is not None:
                cursor.execute("UPDATE employees SET base_salary = %s WHERE employee_id = %s", (new_salary, employee_id))
            conn.commit()
            self.last_error = ""
            return True
        except Exception as error:
            if conn:
                conn.rollback()
            self.last_error = f"Failed to {change_type.lower()}: {error}"
            print(self.last_error)
            return False
        finally:
            if cursor:
                cursor.close()


class AnalyticsManager:
    def __init__(self, db_config):
        self.db = DatabaseConnection()
        self.db_config = db_config

    def get_top_performers_by_department(self):
        conn = self.db.connect(**self.db_config)
        if not conn:
            return []
        
        # Comprehensive query across ALL departments
        query = """
            SELECT 
                d.department_name,
                e.first_name,
                e.last_name,
                f.performance_rating,
                DENSE_RANK() OVER(PARTITION BY d.department_name ORDER BY f.performance_rating DESC) as dept_rank
            FROM hr_olap.Fact_PerformanceReviews f
            JOIN hr_olap.Dim_Employee e ON f.employee_sk = e.employee_sk
            JOIN hr_olap.Dim_Department d ON f.department_sk = d.department_sk
            WHERE e.is_current = TRUE;
        """
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"Error executing OLAP query: {e}")
            return []