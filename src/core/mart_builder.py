def generate_mart_sql(selected_metrics):
    """
    Generates the SQL query to build the Data Mart based on selected metrics.
    """
    
    # Base CTE (Common Table Expression)
    # Always need report_date, users, orders, clicks as base counters
    sql = """
    CREATE OR REPLACE TABLE dm_daily_kpi AS
    WITH daily_stats AS (
        SELECT 
            date_trunc('day', assigned_at) as report_date,
            COUNT(DISTINCT a.user_id) as total_users,
            COUNT(DISTINCT CASE WHEN e.event_name = 'click_banner' THEN e.user_id END) as click_count,
            COUNT(DISTINCT CASE WHEN e.event_name = 'purchase' THEN e.user_id END) as total_orders,
"""
            
    if 'revenue' in selected_metrics:
        sql += "        COALESCE(SUM(CASE WHEN e.event_name = 'purchase' THEN e.value ELSE 0 END), 0) as total_revenue,\n"
    if 'ctr' in selected_metrics:
        sql += "        (COUNT(DISTINCT CASE WHEN e.event_name = 'click_banner' THEN e.user_id END)::FLOAT / NULLIF(COUNT(DISTINCT a.user_id), 0)) as ctr,\n"
    if 'cvr' in selected_metrics:
        sql += "        (COUNT(DISTINCT CASE WHEN e.event_name = 'purchase' THEN e.user_id END)::FLOAT / NULLIF(COUNT(DISTINCT a.user_id), 0)) as cvr,\n"
    if 'aov' in selected_metrics:
        sql += "        COALESCE(SUM(CASE WHEN e.event_name = 'purchase' THEN e.value ELSE 0 END) / NULLIF(COUNT(DISTINCT CASE WHEN e.event_name = 'purchase' THEN e.user_id END), 0), 0) as aov,\n"
    if 'arpu' in selected_metrics:
        sql += "        COALESCE(SUM(CASE WHEN e.event_name = 'purchase' THEN e.value ELSE 0 END) / NULLIF(COUNT(DISTINCT a.user_id), 0), 0) as arpu,\n"
    if 'session_depth' in selected_metrics:
        sql += "        COUNT(e.event_name)::FLOAT / NULLIF(COUNT(DISTINCT a.user_id), 0) as session_depth,\n"

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
    
    if 'revenue' in selected_metrics: sql += "        total_revenue,\n"
    if 'ctr' in selected_metrics: sql += "        ctr,\n"
    if 'cvr' in selected_metrics: sql += "        cvr,\n"
    if 'aov' in selected_metrics: sql += "        aov,\n"
    if 'arpu' in selected_metrics: sql += "        arpu,\n"
    if 'session_depth' in selected_metrics: sql += "        session_depth,\n"

    # Remove trailing comma before updated_at


    sql += """
        CURRENT_TIMESTAMP as updated_at
    FROM daily_stats
    ORDER BY report_date ASC;
    """
    
    return sql.strip()

def generate_mart_diagram(selected_metrics, scale=1.0):
    """
    Generates a Graphviz DOT string to visualize the ETL flow.
    Layout: Left-to-Right (LR) for compact vertical fit.
    """
    # Compact Scaled Dimensions
    fs_graph = max(9, int(11 * scale))
    fs_node = max(9, int(11 * scale))
    fs_schema = max(8, int(10 * scale))
    
    # Tighter spacing for LR
    node_h = 0.5 * scale
    node_sep = 0.2 * scale
    rank_sep = 0.5 * scale  # Distance between ranks (cols)
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
    
    # Horizontal Schema Parts
    schema_label = "{"
    # Row 1: Keys
    schema_label += " 🔑 report_date | 👥 users | 🖱️ clicks | 🛍️ orders "
    
    # Row 2: Metrics (Optional)
    metrics_part = ""
    if 'revenue' in selected_metrics: metrics_part += "| 💰 rev "
    if 'ctr' in selected_metrics: metrics_part += "| 👆 ctr "
    if 'cvr' in selected_metrics: metrics_part += "| 🛒 cvr "
    if 'aov' in selected_metrics: metrics_part += "| 💳 aov "
    if 'arpu' in selected_metrics: metrics_part += "| 👤 arpu "
    if 'session_depth' in selected_metrics: metrics_part += "| ⚡ depth "
    
    if metrics_part:
        schema_label += metrics_part
        
    schema_label += "| 🕒 updated_at }"
    
    dot += f'    schema [label="{schema_label}"]\n'
    dot += f'    mart -> schema [style=dashed, arrowhead=none, color="#94a3b8"]\n'
    dot += "}"
    
    return dot
