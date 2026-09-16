# backend/models.py

# backend/models.py
class Employee:
    def __init__(self, employee_id, first_name, last_name, department_id, job_role, base_salary=5000, salary=None, **details):
        self.employee_id = employee_id
        self.first_name = first_name
        self.last_name = last_name
        self.department_id = department_id
        self.job_role = job_role
        # Accept either base_salary or salary
        self.base_salary = salary if salary is not None else base_salary
        self.salary = self.base_salary
        for field, value in details.items():
            setattr(self, field, value)

class Project:
    def __init__(self, project_id, project_name, client_name, department_id, status):
        self.project_id = project_id
        self.project_name = project_name
        self.client_name = client_name
        self.department_id = department_id
        self.status = status

class Review:
    def __init__(self, review_id, employee_id, review_date, performance_rating):
        self.review_id = review_id
        self.employee_id = employee_id
        self.review_date = review_date
        self.performance_rating = performance_rating