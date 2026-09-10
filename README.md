# Rising Stars - DW Greenfield Project
rising-stars-dw/
├── data/
│   ├── raw/                  # Original WA_Fn-UseC_-HR-Employee-Attrition.csv
│   └── processed/            # Synthesized 100k+ row datasets
├── database/
│   ├── ddl/                  # Table creation scripts (OLTP & OLAP)
│   ├── dml/                  # Initial seed data
│   └── stored_procedures/    # ETL pipelines, CTEs, and Window Functions
├── src/
│   ├── backend/
│   │   ├── db_manager.py     # Singleton DatabaseConnection class
│   │   ├── entities.py       # OOP classes (Employee, Project, Review)
│   │   └── dal.py            # Data Access Layer (EmployeeManager, etc.)
│   ├── etl/
│   │   └── data_synthesizer.py # Faker/Pandas script to scale to 100k+ rows
│   └── frontend/
│       ├── app.py            # Main Streamlit application entry point
│       ├── forms.py          # Data entry forms for onboarding
│       └── dashboards.py     # Plotly/Altair interactive analytics
├── docs/                     # Architecture diagrams (Draw.io/Lucidchart)
├── requirements.txt          # Python dependencies
└── README.md                 # Setup and warehousing logic documentation