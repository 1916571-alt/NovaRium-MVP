# 🎓 NovaRium Edu: A/B Testing Master Class

> **"Don't just read about A/B testing. Do it."**

NovaRium Edu is an interactive simulator that turns you into a Data Analyst.  
Experience the full lifecycle of an experiment, from writing a hypothesis to calculating P-values.

![App Screenshot](https://via.placeholder.com/800x400?text=NovaRium+Edu+Dashboard)

## 🚀 Features

### 1. Hands-on Learning (5-Step Wizard)
Follow the guided path to run a perfect experiment:
-   **Step 1**: Write a hypothesis for the "NovaEats" food delivery app.
-   **Step 2**: Calculate how many users you need (Power Analysis).
-   **Step 3**: See how users are randomly split (Hashing).
-   **Step 4**: Collect real-time logs in a local database.
-   **Step 5**: Analyze SQL results and decide: **Ship or Kill?**

### 2. My Portfolio
-   Save your experiment history.
-   Write "Learning Notes" for every test.
-   Build a portfolio to show future employers.

## 🛠️ Getting Started

### Prerequisites
-   Python 3.8+
-   Pip

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/1916571-alt/NovaRium-MVP.git
    cd NovaRium-MVP
    ```

2.  Install dependencies:
    ```bash
    # Create virtual environment (Optional but Recommended)
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate

    # Install libs
    pip install streamlit duckdb pandas plotly scipy
    ```

3.  Initialize Database:
    ```bash
    python scripts/setup_warehouse.py
    ```

4.  **Run the App**:
    ```bash
    streamlit run scripts/dashboard.py
    ```

## 📂 Project Structure
-   `scripts/dashboard.py`: Main application (Streamlit).
-   `scripts/setup_warehouse.py`: Database initializer.
-   `novarium_local.db`: Local DuckDB file (Auto-created).

---
**NovaRium Edu** - Built for detailed A/B testing education.
