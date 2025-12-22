# NovaRium Edu: A/B Testing Master Class

## 1. Project Overview
NovaRium Edu is an interactive, **educational A/B testing simulator** designed to teach students and junior analysts the complete experimentation workflow. Unlike static dashboards, it offers a hands-on "Wizard" experience that guides users from hypothesis generation to statistical analysis.

## 2. Core Value Proposition
-   **Learning by Doing**: Directly experience the 5-step process (Hypothesis -> Design -> Sampling -> Logging -> Analysis).
-   **Visualizing the Invisible**: See how Hash algorithms divide users and how logs accumulate in a database.
-   **Portfolio Building**: Save experiment results to an archive to demonstrate growth and understanding.

## 3. Key Features

### 🎓 5-Step Master Class (Wizard Mode)
1.  **Hypothesis & Metrics**: Define problems using a Mock App (NovaEats) and select core metrics (CTR, CVR).
2.  **Power Analysis**: Calculate required sample size (`scipy`) based on Alpha, Power, and MDE.
3.  **Sampling**: Visualize deterministic Hash-based traffic allocation.
4.  **Simulation**: Generate realistic event logs (`assignments`, `events`) in real-time.
5.  **Analysis**: Execute SQL queries on DuckDB to aggregate data and calculate P-values.

### 🗄️ My Portfolio (Archive)
-   **History Tracking**: Automatically save every experiment's hypothesis, result, and learning notes.
-   **Growth Evidence**: A dedicated page to review past experiments and "Success/Fail" history.

### 🛠️ Tech Stack
-   **Frontend**: Streamlit (Python components, Session State)
-   **Backend**: DuckDB (Local analytical warehouse)
-   **Statistics**: Scipy (Norm distributions, Z-test)
-   **Visualization**: Plotly (Interactive charts)

## 4. Database Schema
-   **`users`**: Base user pool (demographics).
-   **`orders`**: Historical transaction data.
-   **`assignments`**: Experiment group allocation logs.
-   **`events`**: User behavior logs (clicks, purchases).
-   **`experiments`**: Meta-data archive for completed tests.
