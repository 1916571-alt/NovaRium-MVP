# Product Requirements Document (PRD): NovaRium-MVP

## 1. Project Overview
**NovaRium-MVP** is a local-first data analysis project designed to demonstrate core data analyst competencies—specifically Data Pipeline construction, SQL proficiency, and Logic application—without the need for complex infrastructure. The project aims to prove practical skills through a "Minimum Viable Product" approach that generates, stores, and analyzes business data.

## 2. Objectives
*   **Proof of Competence:** Instantly demonstrate "Data Analyst practical skills" to potential employers.
*   **Simplicity:** Implement using minimal files (1 Python script + 1 SQL file) to ensure easy replication and review.
*   **Focus:** Prioritize demonstrating the 'Flow of Data' and 'Logic of Experimentation' over visual dashboards.

## 3. Scope
The scope allows for the end-to-end simulation of a data environment on a local machine:
1.  **Data Generation:** Creating realistic mock data.
2.  **Warehousing:** Storing data in a local analytical database.
3.  **Analysis:** Deriving insights and validating hypotheses through code and SQL.

## 4. Functional Requirements

### 4.1. Data Generation (The Generator)
*   **Input:** None (Self-generating via script).
*   **Process:** Use Python library `faker` to generate synthetic data reflecting a realistic business domain (e.g., mobile ordering service like Pass Order).
*   **Output:** CSV files stored in a `raw_data/` directory.
    *   `users.csv`: User metadata (Target: approx. 1,000 users).
    *   `orders.csv`: Transactional data history.
    *   `ab_test_logs.csv`: Logs documenting A/B test assignments and interactions.
*   **Data Volume:** Simulation of 3 months of log data.

### 4.2. Local Data Warehouse (The Warehouse)
*   **Technology:** DuckDB (Serverless, embedded SQL OLAP database).
*   **Process:**
    *   Initialize `novarium_local.db`.
    *   Load CSV files into the database using Python (`duckdb.connect`).
*   **Constraint:** No external server installation required; runs strictly within the local Python environment.

### 4.3. Analysis & Verification (The Analysis)
*   **Technology:** SQL, Python (Pandas, SciPy).
*   **Output:** A Jupyter Notebook (`.ipynb`) or summary report markdown.
*   **Key Analytical Tasks:**
    *   **Data Mart Construction:** Create aggregated views/tables using SQL (e.g., User First Order Date, Total Order Count, Retention status).
    *   **Cohort Analysis:** Calculate Retention Rate based on signup weeks.
    *   **Segmentation:** Analyze behavioral differences between user personas (e.g., 'Office Worker' vs 'Student').
    *   **A/B Testing:**
        *   Compare Conversion Rates (CVR) between control and test groups (e.g., Push Notification recipients vs non-recipients).
        *   Calculate Statistical Significance (p-value).
    *   **Business Metrics:** ROI Analysis (Campaign Cost vs Total Revenue).

## 5. Technical Stack
*   **Language:** Python 3.x
*   **Libraries:** `faker` (Generation), `duckdb` (Storage/Query), `pandas` (Manipulation), `scipy` (Statistics).
*   **Environment:** Local Machine (Windows/Mac/Linux compatible).

## 6. Implementation Roadmap
*   **Day 1: Data Generation**
    *   Develop Python script to generate mock users, orders, and logs.
*   **Day 2: Infrastructure & SQL**
    *   Set up DuckDB.
    *   Ingest data.
    *   Write core SQL queries for Retention and RFM analysis.
*   **Day 3: Experimentation & Reporting**
    *   Conduct A/B test analysis.
    *   Draft final insight report.
