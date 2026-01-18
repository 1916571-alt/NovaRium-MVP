"""
Data Mart Builder for NovaRium Edu.

This module provides utilities for generating SQL queries and ETL diagrams
for the daily KPI data mart.
"""
from typing import List


def generate_mart_sql(selected_metrics: List[str]) -> str:
    """
    Generate SQL query to build the Data Mart based on selected metrics.

    Creates a dm_daily_kpi table with daily aggregated statistics from
    assignments and events tables.

    Args:
        selected_metrics: List of metric names to include.
            Supported metrics: 'revenue', 'ctr', 'cvr', 'aov', 'arpu', 'session_depth'

    Returns:
        SQL CREATE TABLE statement as a string.

    Example:
        >>> sql = generate_mart_sql(['revenue', 'cvr'])
        >>> print(sql)  # Returns CREATE TABLE statement with revenue and cvr columns
    """
    # Base CTE with required columns
    sql = """
    CREATE OR REPLACE TABLE dm_daily_kpi AS
    WITH daily_stats AS (
        SELECT
            date_trunc('day', assigned_at) as report_date,
            COUNT(DISTINCT a.user_id) as total_users,
            COUNT(DISTINCT CASE WHEN (e.event_name = 'banner_A' OR e.event_name = 'banner_B') THEN e.user_id END) as click_count,
            COUNT(DISTINCT CASE WHEN e.event_name = 'purchase' THEN e.user_id END) as total_orders,
"""

    # Add optional metric columns
    metric_columns = {
        'revenue': "        COALESCE(SUM(CASE WHEN e.event_name = 'purchase' THEN e.value ELSE 0 END), 0) as total_revenue,\n",
        'ctr': "        (COUNT(DISTINCT CASE WHEN (e.event_name = 'banner_A' OR e.event_name = 'banner_B') THEN e.user_id END)::FLOAT / NULLIF(COUNT(DISTINCT a.user_id), 0)) as ctr,\n",
        'cvr': "        (COUNT(DISTINCT CASE WHEN e.event_name = 'purchase' THEN e.user_id END)::FLOAT / NULLIF(COUNT(DISTINCT a.user_id), 0)) as cvr,\n",
        'aov': "        COALESCE(SUM(CASE WHEN e.event_name = 'purchase' THEN e.value ELSE 0 END) / NULLIF(COUNT(DISTINCT CASE WHEN e.event_name = 'purchase' THEN e.user_id END), 0), 0) as aov,\n",
        'arpu': "        COALESCE(SUM(CASE WHEN e.event_name = 'purchase' THEN e.value ELSE 0 END) / NULLIF(COUNT(DISTINCT a.user_id), 0), 0) as arpu,\n",
        'session_depth': "        COUNT(e.event_name)::FLOAT / NULLIF(COUNT(DISTINCT a.user_id), 0) as session_depth,\n",
    }

    for metric in selected_metrics:
        if metric in metric_columns:
            sql += metric_columns[metric]

    # Remove trailing comma if any conditional metrics were added
    if sql.endswith(",\n"):
        sql = sql.rstrip(",\n") + "\n"

    sql += """
        FROM assignments a
        LEFT JOIN events e ON a.user_id = e.user_id AND DATE_TRUNC('day', e.timestamp) = date_trunc('day', a.assigned_at)
        GROUP BY 1
    )
    SELECT
        report_date,
        total_users,
        click_count,
        total_orders,
"""

    # Add selected metrics to final SELECT
    select_columns = {
        'revenue': "        total_revenue,\n",
        'ctr': "        ctr,\n",
        'cvr': "        cvr,\n",
        'aov': "        aov,\n",
        'arpu': "        arpu,\n",
        'session_depth': "        session_depth,\n",
    }

    for metric in selected_metrics:
        if metric in select_columns:
            sql += select_columns[metric]

    sql += """
        CURRENT_TIMESTAMP as updated_at
    FROM daily_stats
    ORDER BY report_date ASC;
    """

    return sql.strip()


def generate_mart_diagram(selected_metrics: List[str], scale: float = 1.0) -> str:
    """
    Generate a Graphviz DOT string to visualize the ETL flow.

    Creates a left-to-right diagram showing:
    - Source tables (events, assignments)
    - Transformation step (Join & Aggregate)
    - Target mart (dm_daily_kpi)
    - Schema visualization

    Args:
        selected_metrics: List of metric names to show in schema.
            Supported: 'revenue', 'ctr', 'cvr', 'aov', 'arpu', 'session_depth'
        scale: Scaling factor for diagram dimensions (default 1.0)

    Returns:
        Graphviz DOT language string for rendering the diagram.
    """
    # Scaled dimensions
    fs_graph = max(9, int(11 * scale))
    fs_node = max(9, int(11 * scale))
    fs_schema = max(8, int(10 * scale))

    # Spacing parameters
    node_h = 0.5 * scale
    node_sep = 0.2 * scale
    rank_sep = 0.5 * scale
    pad = 0.2 * scale
    penwidth = max(0.8, 1.2 * scale)

    dot = f"""
    digraph ETL {{
        rankdir=LR;
        bgcolor="transparent";
        graph [pad="{pad}", nodesep="{node_sep}", ranksep="{rank_sep}", fontsize="{fs_graph}", fontname="Sans-Serif", splines="ortho", labelloc="t"];
        node [shape=box, style="filled,rounded", fontname="Sans-Serif", fontsize="{fs_node}", height="{node_h}", penwidth="{penwidth}"];
        edge [penwidth="{penwidth}", arrowsize="{0.8*scale}", color="#64748b"];

        # Sources (Left)
        {{rank=same; raw_events; raw_users}}
        node [fillcolor="#E0E7FF", color="#4338ca"]
        raw_events [label="📄 events\\n(Raw Logs)"]
        raw_users [label="👥 assignments\\n(User Data)"]

        # Transformations (Middle)
        node [fillcolor="#F3E8FF", color="#7e22ce", shape=ellipse, height="{node_h}"]
        agg [label="⚙️ Join & Agg"]

        # Mart (Right)
        node [fillcolor="#D1FAE5", color="#059669", shape=folder, height="{node_h}"]
        mart [label="📊 dm_daily_kpi"]

        # Schema (Far Right)
        node [shape=record, fillcolor="#FEF3C7", color="#d97706", height="{node_h*0.6}", fontsize="{fs_schema}"]

        # Edges
        raw_events -> agg
        raw_users -> agg
        agg -> mart
    """

    # Build schema label
    schema_label = _build_schema_label(selected_metrics)

    dot += f'    schema [label="{schema_label}"]\n'
    dot += f'    mart -> schema [style=dashed, arrowhead=none, color="#94a3b8"]\n'
    dot += "}"

    return dot


def _build_schema_label(selected_metrics: List[str]) -> str:
    """
    Build the schema label string for the ETL diagram.

    Args:
        selected_metrics: List of selected metric names.

    Returns:
        Graphviz record label string.
    """
    # Base columns
    schema_label = "{ 🔑 report_date | 👥 users | 🖱️ clicks | 🛍️ orders "

    # Optional metric columns
    metric_icons = {
        'revenue': "| 💰 rev ",
        'ctr': "| 👆 ctr ",
        'cvr': "| 🛒 cvr ",
        'aov': "| 💳 aov ",
        'arpu': "| 👤 arpu ",
        'session_depth': "| ⚡ depth ",
    }

    for metric in selected_metrics:
        if metric in metric_icons:
            schema_label += metric_icons[metric]

    schema_label += "| 🕒 updated_at }"

    return schema_label
