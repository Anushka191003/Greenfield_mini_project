import os
from datetime import date, timedelta

from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import streamlit as st

from backend.dal import AnalyticsManager, EmployeeManager
from backend.db_manager import DatabaseConnection
from backend.models import Employee

load_dotenv()

st.set_page_config(page_title="People Analytics", page_icon="N", layout="wide", initial_sidebar_state="expanded")

# ===============================================================================
# DATABASE CONFIGURATION
# ===============================================================================
DB_CONFIG = {"uri": os.environ["DATABASE_URL"]}

ROOT = os.path.dirname(os.path.abspath(__file__))
SYNTHETIC_DIR = os.path.join(ROOT, "data", "synthetic")
DEPARTMENTS = {
    "DPT-001": "Sales", "DPT-002": "Research & Development", "DPT-003": "Human Resources",
    "DPT-004": "Finance", "DPT-005": "Information Technology", "DPT-006": "Marketing", "DPT-007": "Operations",
}


def inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
        :root { --ink:#f4fbfa; --muted:#9bb5b3; --canvas:#102225; --rail:#142e32; --panel:#1a3438; --field:#49686b; --line:#31575a; --accent:#18c2ad; --accent-warm:#ff936f; }
        html, body, [class*="css"] { font-family:'DM Sans', sans-serif; }
        .stApp { background:radial-gradient(circle at 78% -10%, #285158 0%, var(--canvas) 40%); color:var(--ink); }
        [data-testid="stSidebar"] { background:var(--rail); border-right:1px solid #30343b; }
        [data-testid="stSidebar"] > div:first-child { padding:2rem 1.25rem 1rem; }
        [data-testid="stSidebar"] h1 { font-family:'Space Grotesk', sans-serif; font-size:1.45rem; letter-spacing:-.04em; margin:0 0 2.5rem .5rem; color:#fff; }
        [data-testid="stSidebar"] hr { border-color:#383c43; margin:2.2rem .5rem 1.5rem; }
        [data-testid="stSidebar"] .stRadio label { color:#d9dbe0; font-weight:600; padding:.35rem 0; }
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap:.1rem; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:var(--muted); font-size:.76rem; }
        .block-container { max-width:1440px; padding:3.5rem 4.5rem 5rem; }
        h1, h2, h3 { font-family:'Space Grotesk', sans-serif; letter-spacing:-.045em; color:var(--ink); }
        h1 { font-size:3.2rem !important; margin-bottom:.2rem !important; } h2 { font-size:1.65rem !important; } h3 { font-size:1.15rem !important; }
        .eyebrow { color:var(--accent-warm); text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; font-weight:700; margin-bottom:.45rem; }
        .lede { color:var(--muted); font-size:1.02rem; margin:0 0 2rem; }
        .rule { border-top:1px solid var(--line); margin:2rem 0 1.6rem; }
        .metric { background:linear-gradient(145deg,#272b32,#202329); border:1px solid #3b3f47; border-radius:13px; padding:1.55rem 1.4rem 1.25rem; min-height:126px; }
        .metric .value { font-family:'Space Grotesk'; font-size:2.55rem; font-weight:700; color:#fff; line-height:1; }
        .metric .label { color:#aeb2bb; font-size:.7rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; margin-top:.75rem; }
        .metric .note { color:var(--accent); font-size:.75rem; margin-top:.25rem; }
        .leader-card { background:linear-gradient(145deg,#23454a,#19373b); border:1px solid var(--line); border-top:3px solid; border-radius:10px; padding:.8rem .75rem; margin:.35rem 0 1rem; min-height:116px; }
        .leader-rank { color:var(--accent-warm); font-size:.72rem; font-weight:700; letter-spacing:.08em; }
        .leader-name { color:var(--ink); font-size:.9rem; font-weight:700; margin-top:.35rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .leader-dept { color:var(--muted); font-size:.7rem; margin-top:.15rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .leader-score { color:var(--accent); font-family:'Space Grotesk'; font-size:1.55rem; font-weight:700; margin-top:.45rem; }
        .leader-score span { color:var(--muted); font-family:'DM Sans'; font-size:.68rem; font-weight:400; margin-left:.12rem; }
        .surface { background:rgba(34,37,43,.78); border:1px solid var(--line); border-radius:14px; padding:1.45rem 1.6rem; }
        .schema-title { font-family:'Space Grotesk'; font-weight:700; font-size:1.25rem; margin-bottom:.8rem; }
        .schema-title span { color:#8ee58f; background:#2b4934; border-radius:5px; padding:.1rem .35rem; font-size:1rem; }
        .schema-copy { color:#adb1ba; line-height:1.8; margin:0; }
        .stTextInput label, .stNumberInput label, .stSelectbox label, .stDateInput label, .stTextArea label, .stSlider label { color:#dfe1e5 !important; font-weight:600; }
        .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] { background:#69717e !important; border:0 !important; border-radius:8px !important; color:#fff !important; }
        .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stTextArea textarea:focus { box-shadow:0 0 0 2px var(--accent) !important; }
        .stButton button, .stFormSubmitButton button { width:100%; background:var(--accent); color:#fff; border:0; border-radius:8px; font-weight:700; min-height:2.7rem; }
        .stButton button:hover, .stFormSubmitButton button:hover { background:#36d6c1; color:#082022; }
        [data-testid="stTabs"] button { color:#d7d9df; font-weight:700; } [data-testid="stTabs"] button[aria-selected="true"] { color:var(--accent); }
        [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:10px; }
        @media (max-width: 900px) { .block-container { padding:2.5rem 1.25rem 4rem; } h1 { font-size:2.4rem !important; } }
        </style>
        """, unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def csv_data(filename):
    path = os.path.join(SYNTHETIC_DIR, filename)
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()


def metric(label, value, note=""):
    note_html = f'<div class="note">{note}</div>' if note else ""
    st.markdown(f'<div class="metric"><div class="value">{value}</div><div class="label">{label}</div>{note_html}</div>', unsafe_allow_html=True)


def page_header(kicker, title, subtitle):
    st.markdown(f'<div class="eyebrow">{kicker}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<p class="lede">{subtitle}</p>', unsafe_allow_html=True)


def home_page():
    employees, projects, reviews = csv_data("employees.csv"), csv_data("projects.csv"), csv_data("reviews.csv")
    page_header("Enterprise People Intelligence", "People Analytics", "A practical command center for workforce, projects, and performance")
    cols = st.columns(4)
    with cols[0]: metric("Employee records", f"{len(employees) / 1000:.0f}K+" if len(employees) else "25K+", "OLTP master data")
    with cols[1]: metric("MySQL schemas", "2", "hr_oltp + hr_olap")
    with cols[2]: metric("Historical tracking", "SCD2", "department and salary history")
    with cols[3]: metric("ETL procedures", "5", "warehouse refresh pipeline")
    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="surface"><div class="schema-title">OLTP Schema <span>hr_oltp</span></div><p class="schema-copy">Departments - master department list<br>Employees - workforce records<br>Projects - company projects<br>Assignments - project bridge table<br>Reviews - performance history<br>Employee history - audit trail</p></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="surface"><div class="schema-title">OLAP Star Schema <span>hr_olap</span></div><p class="schema-copy">Fact_PerformanceReviews - central fact<br>Dim_Employee - SCD Type 2<br>Dim_Department - department dimension<br>Dim_Project - project dimension<br>Dim_Date - calendar dimension</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    st.subheader("Warehouse pulse")
    pulse = pd.DataFrame({"Dataset": ["Employees", "Projects", "Reviews", "History"], "Records": [len(employees), len(projects), len(reviews), len(csv_data("employee_history.csv"))]})
    fig = px.bar(pulse, x="Dataset", y="Records", color="Dataset", color_discrete_sequence=["#18c2ad", "#ff936f", "#8ee58f", "#d7a8ff"])
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=290)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def employee_page():
    page_header("People operations", "Employee workspace", "Create, search, and manage workforce changes")
    new_tab, directory_tab, update_tab, history_tab = st.tabs([
        "New Employee", "Directory", "Update Employee Details", "Employee History"
    ])
    
    # --- TAB 1: NEW EMPLOYEE ---
    with new_tab:
        st.subheader("New employee details")
        with st.form("new_employee"):
            c1, c2 = st.columns(2, gap="large")
            with c1:
                first = st.text_input("First name*")
                email = st.text_input("Email")
                gender = st.selectbox("Gender", ["Male", "Female", "Non-binary", "Prefer not to say"])
                department = st.selectbox("Department*", list(DEPARTMENTS), format_func=lambda key: DEPARTMENTS[key])
                job_level = st.slider("Job level", 1, 5, 2)
                salary = st.number_input("Monthly income ($)*", min_value=0, value=5000, step=500)
            with c2:
                last = st.text_input("Last name*")
                phone = st.text_input("Phone")
                age = st.number_input("Age*", min_value=18, max_value=80, value=28)
                role = st.text_input("Job role*", value="Analyst")
                education = st.slider("Education level (1-5)", 1, 5, 3)
                education_field = st.selectbox("Education field", ["Life Sciences", "Medical", "Marketing", "Technical Degree", "Human Resources", "Other"])
            c3, c4, c5 = st.columns(3)
            with c3: hire_date = st.date_input("Hire date*", value=date.today())
            with c4: marital = st.selectbox("Marital status", ["Single", "Married", "Divorced"])
            with c5: distance = st.number_input("Distance from home (km)", min_value=0, value=10)
            submitted = st.form_submit_button("Create employee")
            
        if submitted:
            manager = EmployeeManager(DB_CONFIG)
            if not first.strip() or not last.strip() or not role.strip():
                st.error("First name, last name, and job role are required.")
            else:
                new_emp = Employee(
                    employee_id=0,  # Dynamically replaced inside dal.py add_employee
                    first_name=first.strip(),
                    last_name=last.strip(),
                    department_id=department,
                    job_role=role.strip(),
                    base_salary=salary,
                    gender=gender,
                    date_of_birth=date.today() - timedelta(days=age * 365),
                    marital_status=marital,
                    distance_from_home=distance,
                    education_level=education,
                    education_field=education_field,
                    hire_date=hire_date,
                    job_level=job_level,
                    overtime_eligible="True",
                    stock_option_level=0,
                    total_working_years=0,
                    num_companies_worked=0,
                    business_travel="Rarely",
                    is_active="True",
                )
                success = manager.add_employee(new_emp)
                if success:
                    st.cache_data.clear()
                    st.success(f"{first} {last} was added to the database successfully with ID {new_emp.employee_id}!")
                else:
                    st.error(getattr(manager, 'last_error', None) or "The employee could not be saved.")

    # --- TAB 2: DIRECTORY ---
    with directory_tab:
        st.subheader("Employee directory")
        try:
            employees = pd.DataFrame(EmployeeManager(DB_CONFIG).get_employees())
        except Exception as error:
            st.error(f"Unable to load employees from Aiven: {error}")
            employees = pd.DataFrame()
        if employees.empty:
            st.info("No employee data is available yet.")
        else:
            search = st.text_input("Search by name or role", placeholder="e.g. analyst")
            department_filter = st.selectbox("Department filter", ["All departments"] + list(DEPARTMENTS.values()))
            visible = employees.copy()
            visible["department_name"] = visible["department_id"].map(DEPARTMENTS).fillna(visible["department_id"])
            if search:
                haystack = visible[["first_name", "last_name", "job_role"]].fillna("").astype(str).agg(" ".join, axis=1)
                visible = visible[haystack.str.contains(search, case=False, na=False)]
            if department_filter != "All departments":
                visible = visible[visible["department_name"] == department_filter]
            st.caption(f"Showing {min(len(visible), 100)} of {len(visible):,} matching employees")
            st.dataframe(visible.head(100), use_container_width=True, hide_index=True)

    # --- TAB 3: CONSOLIDATED UPDATE EMPLOYEE DETAILS ---
    with update_tab:
        st.subheader("Update Master Record (OLTP)")
        st.markdown("Modify an employee's department, designation (role), monthly income, and status directly in `hr_oltp.employees`.")
        
        with st.form("unified_employee_update"):
            col_id, col_status = st.columns([2, 1])
            with col_id:
                emp_id = st.number_input("Employee ID*", min_value=1, value=1, step=1)
            with col_status:
                is_active = st.checkbox("Active Employee", value=True)
                
            col_dept, col_role, col_sal = st.columns(3)
            with col_dept:
                new_dept = st.selectbox("New Department*", list(DEPARTMENTS), format_func=lambda key: DEPARTMENTS[key])
            with col_role:
                new_role = st.text_input("New Designation / Job Role*", value="Senior Analyst")
            with col_sal:
                new_salary = st.number_input("New Monthly Salary ($)*", min_value=0, value=6500, step=500)
                
            apply_update = st.form_submit_button("Update Employee Record")
            
        if apply_update:
            if not new_role.strip():
                st.error("Designation / Job Role cannot be empty.")
            else:
                manager = EmployeeManager(DB_CONFIG)
                success = manager.update_employee_details(
                    employee_id=emp_id,
                    new_department_id=new_dept,
                    new_job_role=new_role.strip(),
                    new_salary=new_salary,
                    is_active=is_active
                )
                if success:
                    st.cache_data.clear()
                    st.success(f"Employee ID {emp_id} successfully updated in OLTP! (Department: {DEPARTMENTS[new_dept]}, Role: {new_role}, Salary: ${new_salary:,.0f})")
                else:
                    st.error(getattr(manager, 'last_error', None) or "Failed to update employee record in database.")

    # --- TAB 4: EMPLOYEE HISTORY ---
    with history_tab:
        st.subheader("Employee history")
        st.caption("Review the department, designation, level, and salary recorded before each change.")
        with st.form("employee_history_lookup"):
            history_employee_id = st.number_input("Employee ID*", min_value=1, value=1, step=1)
            view_history = st.form_submit_button("View employee history")

        if view_history:
            manager = EmployeeManager(DB_CONFIG)
            history = manager.get_employee_history(history_employee_id)

            if history:
                history_frame = pd.DataFrame(history)
            else:
                history_frame = csv_data("employee_history.csv")
                if not history_frame.empty:
                    history_frame = history_frame[
                        pd.to_numeric(history_frame["employee_id"], errors="coerce") == history_employee_id
                    ].copy()
                    if not history_frame.empty:
                        history_frame["old_department_name"] = history_frame["old_department_id"].map(DEPARTMENTS).fillna(
                            history_frame["old_department_id"]
                        )

            if history_frame.empty:
                message = manager.last_error or f"No history was found for employee ID {history_employee_id}."
                st.info(message)
            else:
                display_history = history_frame.rename(columns={
                    "history_id": "History ID",
                    "employee_id": "Employee ID",
                    "change_date": "Change date",
                    "change_type": "Change type",
                    "old_department_name": "Previous department",
                    "old_department_id": "Previous department ID",
                    "old_job_role": "Previous designation",
                    "old_job_level": "Previous job level",
                    "old_base_salary": "Previous salary",
                })
                columns = [
                    "History ID", "Employee ID", "Change date", "Change type",
                    "Previous department", "Previous department ID", "Previous designation",
                    "Previous job level", "Previous salary",
                ]
                st.dataframe(display_history[columns], use_container_width=True, hide_index=True)


def projects_page():
    page_header("Delivery operations", "Projects", "Plan initiatives, assign employees, and review the delivery portfolio")
    create_tab, assign_tab, view_tab = st.tabs(["New Project", "Assign Employee", "View Projects"])
    
    with create_tab:
        st.subheader("Create new project")
        with st.form("new_project"):
            c1, c2 = st.columns(2, gap="large")
            with c1:
                name = st.text_input("Project name*")
                client = st.text_input("Client name*")
                department = st.selectbox("Department*", list(DEPARTMENTS), format_func=lambda key: DEPARTMENTS[key], key="project_department")
                start = st.date_input("Start date*", value=date.today())
                budget = st.number_input("Budget ($)", min_value=0, value=100000, step=10000)
            with c2:
                status = st.selectbox("Status", ["Planning", "Active", "On Hold", "Completed"])
                end = st.date_input("End date (optional)", value=None)
                description = st.text_area("Description")
            created = st.form_submit_button("Create project")
            
        if created:
            if not name.strip() or not client.strip():
                st.error("Project name and client name are required.")
            else:
                project_id = f"PRJ-{int(pd.Timestamp.now().timestamp())}"[-15:]
                manager = EmployeeManager(DB_CONFIG)
                ok = manager.create_project(project_id, department, name.strip(), client.strip(), start, end if status == "Completed" else None, status)
                if ok:
                    csv_data.clear()
                    st.success(f"{name} was created with ID {project_id}.")
                else:
                    st.error(getattr(manager, 'last_error', None) or "Project creation failed.")
                    
    with assign_tab:
        st.subheader("Assign employee to project")
        projects = csv_data("projects.csv")
        options = projects["project_id"].astype(str).tolist() if not projects.empty and "project_id" in projects else ["PRJ-0001"]
        with st.form("assignment"):
            project = st.selectbox("Select project*", options)
            employee_id = st.number_input("Employee ID*", min_value=1, value=1, step=1)
            role = st.selectbox("Role", ["Lead", "Contributor", "Reviewer", "Consultant"])
            allocation = st.slider("Allocation percentage", 0, 100, 50, step=25)
            assigned_date = st.date_input("Assigned date", value=date.today())
            assigned = st.form_submit_button("Assign employee")
            
        if assigned:
            assignment_id = f"ASN-{int(pd.Timestamp.now().timestamp())}"[-15:]
            manager = EmployeeManager(DB_CONFIG)
            ok = manager.create_assignment(assignment_id, employee_id, project, role, allocation, assigned_date, None)
            if ok:
                csv_data.clear()
                st.success(f"Employee {employee_id} assigned to {project}.")
            else:
                st.error(getattr(manager, 'last_error', None) or "Assignment failed.")
                
    with view_tab:
        st.subheader("All projects")
        projects = csv_data("projects.csv")
        if not projects.empty:
            st.dataframe(projects.head(100), use_container_width=True, hide_index=True)
        else:
            st.info("No project data is available yet.")


def reviews_page():
    page_header("Talent development", "Performance Reviews", "Capture structured feedback and keep a clear view of performance history")
    submit_tab, view_tab = st.tabs(["Submit Review", "View Reviews"])
    
    with submit_tab:
        st.subheader("Submit a performance review")
        st.info("Ratings use a 1-4 scale: 1 Poor, 2 Below Average, 3 Excellent, 4 Outstanding.")
        with st.form("review_form"):
            c1, c2 = st.columns(2, gap="large")
            with c1:
                employee_id = st.number_input("Employee ID*", min_value=1, value=1, step=1)
                review_year = st.number_input("Review year*", min_value=2015, max_value=2030, value=date.today().year)
                reviewer = st.number_input("Reviewer (manager) ID", min_value=0, value=0, step=1)
                performance = st.slider("Performance rating", 1, 4, 3)
                job = st.slider("Job satisfaction", 1, 4, 3)
                environment = st.slider("Environment satisfaction", 1, 4, 3)
            with c2:
                review_date = st.date_input("Review date*", value=date.today())
                quarter = st.selectbox("Quarter", [1, 2, 3, 4])
                relationship = st.slider("Relationship satisfaction", 1, 4, 3)
                work_life = st.slider("Work-life balance", 1, 4, 3)
                involvement = st.slider("Job involvement", 1, 4, 3)
                comments = st.text_area("Comments / notes")
            submitted = st.form_submit_button("Submit review")
            
        if submitted:
            review_id = f"REV-{int(pd.Timestamp.now().timestamp())}"[-15:]
            manager = EmployeeManager(DB_CONFIG)
            ok = manager.create_review(review_id, employee_id, review_date, performance, job, environment, relationship, involvement, work_life, 0, 0)
            if ok:
                csv_data.clear()
                st.success(f"Review for employee {employee_id} submitted successfully.")
            else:
                st.error(getattr(manager, 'last_error', None) or "Review submission failed.")
                
    with view_tab:
        st.subheader("Review history")
        reviews = csv_data("reviews.csv")
        if not reviews.empty:
            st.dataframe(reviews.head(100), use_container_width=True, hide_index=True)
        else:
            st.info("No review records are available yet.")


def analytics_page():
    page_header("Decision support", "Analytics Dashboard", "Explore performance, workforce risk, and delivery pressure from your warehouse data")
    
    # Fetch live OLAP data
    data = AnalyticsManager(DB_CONFIG).get_top_performers_by_department()
    df = pd.DataFrame(data)
    source_label = "live OLAP query"
    
    # Fallback if DB returns empty
    if df.empty:
        reviews = csv_data("reviews.csv")
        employees = csv_data("employees.csv")
        departments = csv_data("departments.csv")
        if reviews.empty or employees.empty:
            st.warning("No analytics data found. Check the MySQL connection or confirm the generated CSV files exist.")
            return
        df = reviews.merge(employees[["employee_id", "first_name", "last_name", "department_id"]], on="employee_id", how="left")
        df = df.merge(departments, on="department_id", how="left")
        df["department_name"] = df["department_name"].fillna(df["department_id"])
        df["dept_rank"] = df.groupby("department_name")["performance_rating"].rank(method="dense", ascending=False).astype(int)
        source_label = "generated CSV fallback"

    # Data Type Enforcement
    df["department_name"] = df["department_name"].astype(str)
    df["first_name"] = df["first_name"].astype(str)
    df["last_name"] = df["last_name"].astype(str)
    df["performance_rating"] = pd.to_numeric(df["performance_rating"], errors="coerce").astype(float)
    df["dept_rank"] = pd.to_numeric(df["dept_rank"], errors="coerce").fillna(0).astype(int)

    # Top KPI Metrics
    cols = st.columns(3)
    with cols[0]: metric("Total Employees Reviewed", len(df), source_label)
    with cols[1]: metric("Departments", df["department_name"].nunique(), "represented in the warehouse")
    with cols[2]: metric("Average Rating", f'{df["performance_rating"].mean():.1f}', "across all reviews")

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    performance_tab, trend_tab, risk_tab = st.tabs(["Performance", "Year-over-year trends", "Risk & bottlenecks"])
    
    with performance_tab:
        chart_col, table_col = st.columns([1.1, 0.9], gap="large")
        
        # --- COMBINED PERFORMANCE ANALYSIS FOR ALL EMPLOYEES ---
        with chart_col:
            st.subheader("Combined Performance Distribution (All Departments)")
            fig = px.box(
                df, 
                x="department_name", 
                y="performance_rating", 
                color="department_name",
                labels={"department_name": "Department", "performance_rating": "Performance Rating"},
                color_discrete_sequence=["#18c2ad", "#ff936f", "#8ee58f", "#d7a8ff", "#f6c85f", "#4bc0c0", "#ff6384"]
            )
            fig.update_layout(
                template="plotly_dark", 
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)", 
                showlegend=False, 
                margin=dict(l=0, r=0, t=10, b=0), 
                height=420
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # --- TOP PERFORMERS LEADERBOARD & ALL DEPARTMENTS LISTING ---
        with table_col:
            st.subheader("Top Performers Leaderboard")
            filter_col, count_col = st.columns([1.5, 1])
            
            all_departments = sorted(df["department_name"].dropna().unique().tolist())
            
            with filter_col:
                department_filter = st.selectbox(
                    "Select Department",
                    ["All departments"] + all_departments,
                    index=0,  # Default to "All departments"
                    key="performer_department",
                )
            with count_col:
                display_count = st.slider("Show Top", 5, 50, 10, key="performer_count")

            leaderboard = df.copy()
            if department_filter != "All departments":
                leaderboard = leaderboard[leaderboard["department_name"] == department_filter]
            
            leaderboard = leaderboard.sort_values(["performance_rating", "dept_rank"], ascending=[False, True]).reset_index(drop=True)

            podium = leaderboard.head(3)
            if not podium.empty:
                podium_cols = st.columns(len(podium))
                podium_colors = ["#ff936f", "#18c2ad", "#d7a8ff"]
                for position, (_, performer) in enumerate(podium.iterrows()):
                    full_name = f"{performer['first_name']} {performer['last_name']}"
                    with podium_cols[position]:
                        st.markdown(
                            f'''<div class="leader-card" style="border-top-color:{podium_colors[position]}">
                            <div class="leader-rank">#{position + 1}</div>
                            <div class="leader-name">{full_name}</div>
                            <div class="leader-dept">{performer['department_name']}</div>
                            <div class="leader-score">{performer['performance_rating']:.1f}<span>/5</span></div>
                            </div>''',
                            unsafe_allow_html=True,
                        )

            table_display = leaderboard.head(display_count)
            table = table_display.rename(columns={
                "dept_rank": "Rank", "first_name": "First name", "last_name": "Last name",
                "department_name": "Department", "performance_rating": "Rating",
            })[["Rank", "First name", "Last name", "Department", "Rating"]]
            
            st.dataframe(
                table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank": st.column_config.NumberColumn("Rank", format="#%d", width="small"),
                    "Rating": st.column_config.ProgressColumn("Rating", min_value=0, max_value=5, format="%.1f", width="medium"),
                },
            )

    with trend_tab:
        reviews = csv_data("reviews.csv")
        if reviews.empty:
            st.info("Review history is not available.")
        else:
            reviews["review_date"] = pd.to_datetime(reviews["review_date"], errors="coerce")
            trend = reviews.dropna(subset=["review_date"]).assign(year=lambda frame: frame["review_date"].dt.year).groupby("year", as_index=False)["performance_rating"].mean()
            fig = px.line(trend, x="year", y="performance_rating", markers=True, labels={"performance_rating": "Average rating", "year": "Review year"})
            fig.update_traces(line_color="#18c2ad", marker_color="#ff936f", line_width=3)
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=360)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.dataframe(trend, use_container_width=True, hide_index=True)

    with risk_tab:
        employees = csv_data("employees.csv")
        projects = csv_data("projects.csv")
        assignments = csv_data("assignments.csv")
        risk_col, bottleneck_col = st.columns(2, gap="large")
        with risk_col:
            st.subheader("Attrition risk watch")
            if employees.empty:
                st.info("Employee risk data is not available.")
            else:
                risk = employees.copy()
                inactive = ~risk["is_active"].astype(str).str.lower().isin(["true", "1", "yes"])
                overtime = risk["overtime_eligible"].astype(str).str.lower().isin(["true", "1", "yes"])
                frequent_travel = risk["business_travel"].astype(str).str.lower().isin(["frequently", "travel_frequently"])
                long_commute = pd.to_numeric(risk["distance_from_home"], errors="coerce").fillna(0).gt(20)
                no_stock = pd.to_numeric(risk["stock_option_level"], errors="coerce").fillna(0).eq(0)
                risk["risk_score"] = inactive.astype(int) * 60 + overtime.astype(int) * 20 + frequent_travel.astype(int) * 10 + long_commute.astype(int) * 5 + no_stock.astype(int) * 5
                risk["risk_band"] = pd.cut(risk["risk_score"], [-1, 20, 50, 100], labels=["Low", "Watch", "High"])
                st.dataframe(risk.sort_values("risk_score", ascending=False)[["employee_id", "first_name", "last_name", "job_role", "risk_score", "risk_band"]].head(25), use_container_width=True, hide_index=True)
        with bottleneck_col:
            st.subheader("Project pressure")
            if projects.empty or assignments.empty:
                st.info("Project assignment data is not available.")
            else:
                pressure = assignments.groupby("project_id", as_index=False).agg(assignments=("assignment_id", "count"), allocation=("allocation_percentage", "sum"))
                pressure = pressure.merge(projects[["project_id", "project_name", "status"]], on="project_id", how="left").sort_values("assignments", ascending=False)
                st.dataframe(pressure.head(25), use_container_width=True, hide_index=True)


inject_styles()
st.sidebar.title("Analytics Workspace")
page = st.sidebar.radio("Navigate", ["Home", "Onboard Employee", "Projects", "Performance Review", "Analytics Dashboard"], label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.markdown("People intelligence workspace v1.0")

if page == "Home": home_page()
elif page == "Onboard Employee": employee_page()
elif page == "Projects": projects_page()
elif page == "Performance Review": reviews_page()
else: analytics_page()