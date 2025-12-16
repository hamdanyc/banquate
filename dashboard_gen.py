import pandas as pd
import json

def get_table_id(r, c, cols):
    """Calculates table number based on grid position (1-based index)."""
    return (r * cols) + (c + 1)

def generate_dashboard_html(df, rows, cols):
    """
    Generates a standalone HTML file string representing the current grid state.
    """
    # --- Prepare Data (Logic Copied/Adapted from app.py) ---
    table_map = {}
    grouped = df.groupby('table_number')
    for tid, group in grouped:
        # Use first row for group info, essentially
        first_row = group.iloc[0]
        gp_name = str(first_row['gp_name']) if 'gp_name' in group.columns and pd.notna(first_row['gp_name']) else 'Unknown'
        
        table_map[tid] = {
            'occupied': True,
            'group': gp_name,
            'count': len(group)
        }
        
    grid_data = []
    for r in range(rows):
        for c in range(cols):
            tid = get_table_id(r, c, cols)
            data = table_map.get(tid, {'occupied': False, 'group': '', 'count': 0})
            grid_data.append({
                'id': tid,
                'occupied': data['occupied'],
                'group': data['group'],
                'count': data['count']
            })

    # Serialize data for JS injection
    json_data = json.dumps({
        "tables": grid_data,
        "rows": rows,
        "cols": cols,
        "mode": "View",  # Default to View/Read-only
        "selectedId": None
    })

    # --- HTML Template ---
    # We inline the styles and scripts from grid_component/index.html
    # but modify the script to load data immediately.
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Banquet Dashboard</title>
    <style>
        body {{
            font-family: 'Source Sans Pro', sans-serif; /* Streamlit default-ish */
            margin: 0;
            padding: 20px;
            background-color: #f0f2f6; /* Light gray background */
        }}

        h1 {{
            text-align: center;
            color: #31333F;
            margin-bottom: 20px;
        }}

        #grid-container {{
            display: grid;
            gap: 10px;
            padding: 10px;
            margin: 0 auto;
            max-width: 100%;
            /* grid-template-columns set by JS */
        }}

        .table-box {{
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 5px;
            text-align: center;
            height: 110px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background-color: #fff;
            color: #333;
            transition: transform 0.1s, box-shadow 0.1s;
            position: relative;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .table-box.occupied {{
            background-color: #00bcd4;
            color: white;
            border-color: #008ba3;
        }}

        .table-box.vacant {{
            background-color: #e0e0e0;
            color: #aaa;
            border-style: dashed;
        }}

        .table-id {{
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 4px;
        }}

        .group-name {{
            font-weight: bold;
            font-size: 0.9em;
            line-height: 1.1;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            max-height: 2.3em;
        }}

        .guest-count {{
            margin-top: 5px;
            font-size: 0.85em;
            opacity: 0.95;
            background: rgba(0,0,0,0.1);
            padding: 2px 6px;
            border-radius: 10px;
        }}
        
        #footer {{
             text-align: center;
             margin-top: 30px;
             color: #666;
             font-size: 0.9em;
        }}
    </style>
</head>
<body>

    <h1>🍽️ Banquet Seating Dashboard</h1>
    <div id="grid-container"></div>
    <div id="footer">Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</div>

    <script>
        // Injected Data
        const initialData = {json_data};

        function renderGrid(data) {{
            const {{ tables, rows, cols }} = data;
            
            const container = document.getElementById('grid-container');
            
            // Adjust grid layout
            container.style.gridTemplateColumns = `repeat(${{cols}}, 1fr)`;
            // Approximate max width calculator to keep boxes square-ish if wanted, 
            // but filling width is usually fine.
            
            container.innerHTML = '';

            tables.forEach(table => {{
                const div = document.createElement('div');
                div.className = `table-box ${{table.occupied ? 'occupied' : 'vacant'}}`;
                div.id = `table-${{table.id}}`;
                
                div.innerHTML = `
                    <div class="table-id">${{table.id}}</div>
                    <div class="group-name">${{table.occupied ? table.group : 'Vacant'}}</div>
                    ${{table.occupied ? `<div class="guest-count">${{table.count}} pax</div>` : ''}}
                `;
                
                // Optional: Add simple click to show details if we wanted to embed more data
                // For now, static display.
                
                container.appendChild(div);
            }});
        }}

        // Initialize immediately
        document.addEventListener('DOMContentLoaded', () => {{
            renderGrid(initialData);
        }});
    </script>
</body>
</html>
    """
    return html_content
