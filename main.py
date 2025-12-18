import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import plotly.graph_objects as go
import sheets_loader
import plotly.express as px
from pdf_gen import generate_table_summary, generate_floor_plan_layout
import simulation_utils

# --- Configuration ---
# Google Sheets Configuration
SHEET_URL = "https://docs.google.com/spreadsheets/d/1twmu4Ktr9l_798eoeXkfcctWzs3u6BzYlpd8Q_cu0lY/edit?usp=sharing"
WORKSHEET_INDEX = 0  # First worksheet (gid=0)
DEFAULT_TARGET = 500
DEFAULT_ROWS = 7
DEFAULT_COLS = 9

# --- Component Definition ---
parent_dir = os.path.dirname(os.path.abspath(__file__))
component_path = os.path.join(parent_dir, "grid_component")
custom_grid = components.declare_component("banquet_grid", path=component_path)

# --- Data Loading ---
def load_data():
    """Load guest data from Google Sheets"""
    try:
        df = sheets_loader.load_from_google_sheets(SHEET_URL, WORKSHEET_INDEX)
        if 'table_number' in df.columns:
            df['table_number'] = pd.to_numeric(df['table_number'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Error loading data from Google Sheets: {e}")
        st.info("Please ensure the Google Sheet is shared with 'Anyone with the link can view'")
        return pd.DataFrame(columns=["table_number", "seat", "name", "menu", "gp_id", "gp_name"])

def get_table_id_sequential(r, c, cols):
    """Standard sequential numbering: 1, 2, 3... across rows."""
    return (r * cols) + (c + 1)

def get_table_id_oddeven(r, c, cols):
    """
    Arranges odd numbers on the left and even numbers on the right for each row.
    Example (Cols=4): 1, 3 | 2, 4
    """
    start_num = (r * cols) + 1
    end_num = (r + 1) * cols
    
    # Generate all numbers for this row
    row_nums = range(start_num, end_num + 1)
    odds = [n for n in row_nums if n % 2 != 0]
    evens = [n for n in row_nums if n % 2 == 0]
    
    # Combined sequence: Odds first, then Evens
    # This places Odds in the first columns (Left) and Evens in the later columns (Right)
    sorted_nums = odds + evens
    
    return sorted_nums[c]

# --- Main Dashboard ---
def main():
    st.set_page_config(layout="wide", page_title="Banquet Command Center")

    # Styling
    st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        border: 1px solid #dcdcdc;
        padding: 10px 20px;
        border-radius: 10px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.05);
    }
    h1 { margin-bottom: 0.5rem; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Banquet Performance Dashboard")
    
    # Load Data
    df = load_data()

    # --- Sidebar (Optional / Minimal) ---
    st.sidebar.header("Display Options")
    
    # Layout Selector
    layout_mode = st.sidebar.radio(
        "Numbering Layout", 
        ["Sequential", "Odd/Even Split"],
        index=0,
        help="Sequential: 1,2,3,4...\nOdd/Even: 1,3,5... | 2,4,6..."
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("🏗️ Simulation")
    
    with st.sidebar.expander("Simulate Layout Change"):
        insert_input = st.text_input(
            "Insert New Tables After (e.g. 7, 13)",
            value="7",
            help="Enter table numbers separated by commas."
        )
        
        if st.button("Simulate Change"):
            # Parse input
            try:
                insert_after_ids = [int(x.strip()) for x in insert_input.split(',') if x.strip().isdigit()]
            except:
                insert_after_ids = []
            
            if not insert_after_ids:
                 st.sidebar.warning("Please enter valid table numbers.")
            else:
                try:
                    # 1. Run Simulation Logic
                    sim_df, new_order, new_ids = simulation_utils.simulate_table_addition(df, insert_after_ids)
                    
                    # 2. Generate Summary PDF
                    pdf_buffer = generate_table_summary(sim_df, table_order=new_order)
                    
                    # 3. Generate Floor Plan PDF
                    fp_buffer = generate_floor_plan_layout(sim_df, new_order, DEFAULT_ROWS, DEFAULT_COLS)
                    
                    st.sidebar.success(f"Generated! New Tables: {new_ids}")
                    
                    st.sidebar.download_button(
                        label="📄 Download Simulation PDF",
                        data=pdf_buffer,
                        file_name=f"simulated_summary.pdf",
                        mime="application/pdf"
                    )
                    
                    st.sidebar.download_button(
                        label="🗺️ Download Floor Plan PDF",
                        data=fp_buffer,
                        file_name=f"simulated_floor_plan.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.sidebar.error(f"Simulation failed: {e}")

    # Use Defaults directly
    target_guests = DEFAULT_TARGET
    rows = DEFAULT_ROWS
    cols = DEFAULT_COLS

    # --- HEAD TABLE SECTION ---
    st.subheader("👑 Meja DiRaja")
    
    # Data for head tables (Static for now as requested)
    head_tables = [
        {'id': 1001, 'occupied': True, 'group': 'DiRaja', 'count': 8}, # ID arbitrary
        {'id': 1002, 'occupied': True, 'group': 'DiRaja', 'count': 8}
    ]
    
    # Centering using columns: 2 tables width vs 9 tables width ~ 2/9 scale
    # Layout: [Spacer] [HeadGrid] [Spacer]
    hc1, hc2, hc3 = st.columns([3.5, 2, 3.5]) 
    with hc2:
        custom_grid(
            tables=head_tables,
            rows=1,
            cols=2,
            mode="View",
            selectedId=None,
            key="head_table_grid"
        )


    # --- TOP SECTION: GRID VIEW ---
    st.subheader("📍 Live Floor Plan")
    
    # Prepare Grid Data
    table_map = {}
    grouped = df.groupby('table_number')
    for tid, group in grouped:
        occupants = len(group)
        gp_name = "Unknown"
        if 'gp_name' in group.columns and not group['gp_name'].isna().all():
             gp_name = group['gp_name'].dropna().iloc[0]
        
        table_map[tid] = {
            'occupied': True,
            'group': str(gp_name),
            'count': occupants
        }
        
    grid_data = []
    for r in range(rows):
        for c in range(cols):
            if layout_mode == "Odd/Even Split":
                tid = get_table_id_oddeven(r, c, cols)
            else:
                tid = get_table_id_sequential(r, c, cols)
                
            data = table_map.get(tid, {'occupied': False, 'group': '', 'count': 0})
            grid_data.append({
                'id': tid,
                'occupied': data['occupied'],
                'group': data['group'],
                'count': data['count']
            })

    # Render Component (Read-Only Mode)
    custom_grid(
        tables=grid_data,
        rows=rows,
        cols=cols,
        mode="View", 
        selectedId=None,
        key=f"dashboard_grid_{layout_mode}" # Update key to force redraw on change
    )

    st.markdown("---")

    # --- MIDDLE SECTION: METRICS & GAUGE ---
    
    # KPIs
    total_guests = len(df)
    if not df.empty:
        total_tables = df[df['table_number'] > 0]['table_number'].nunique()
    else:
        total_tables = 0
    
    performance_pct = (total_guests / target_guests) * 100
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("📈 Key Metrics")
        st.write("") # Spacer
        
        m1, m2 = st.columns(2)
        with m1:
            st.metric(
                label="Total Guests", 
                value=f"{total_guests}", 
                delta=f"{total_guests - target_guests} vs Target"
            )
        with m2:
            st.metric(
                label="Reserved Tables", 
                value=f"{total_tables}",
                help="Active tables with guests assigned."
            )
            
        st.write("")
        st.info(f"Targeting **{target_guests}** Total Guests")

    with c2:
        st.subheader("🎯 Target Performance")
        
        # Plotly Gauge Chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = total_guests,
            delta = {'reference': target_guests, 'position': "top"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Guest Count Status"},
            gauge = {
                'axis': {'range': [None, max(target_guests * 1.2, total_guests * 1.1)]},
                'bar': {'color': "#00bcd4"},
                'steps': [
                    {'range': [0, target_guests * 0.5], 'color': "#ffebee"},
                    {'range': [target_guests * 0.5, target_guests * 0.9], 'color': "#fff3e0"},
                    {'range': [target_guests * 0.9, max(target_guests * 1.2, total_guests * 1.1)], 'color': "#e8f5e9"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': target_guests
                }
            }
        ))
        fig.update_layout(height=250, margin=dict(t=30, b=10, l=30, r=40))
        st.plotly_chart(fig, width="stretch")

    st.markdown("---")

    # --- BOTTOM SECTION: MENU ---
    st.subheader("🍽️ Menu Analysis")
    
    if not df.empty and 'menu' in df.columns:
        menu_counts = df['menu'].fillna('Unknown').value_counts().reset_index()
        menu_counts.columns = ['Menu Type', 'Count']
        
        # Calculate percentage
        menu_counts['Percentage'] = (menu_counts['Count'] / total_guests * 100).round(1)
        
        mc1, mc2 = st.columns([2, 1])
        
        with mc1:
             st.dataframe(
                menu_counts, 
                width="stretch",
                hide_index=True,
                column_config={
                    "Count": st.column_config.ProgressColumn(
                        "Count",
                        format="%d",
                        min_value=0,
                        max_value=int(menu_counts['Count'].max()) if not menu_counts.empty else 100,
                    ),
                    "Percentage": st.column_config.NumberColumn(
                        "%",
                        format="%.1f%%"
                    )
                }
            )
            
        with mc2:
            fig_pie = px.pie(menu_counts, values='Count', names='Menu Type', hole=0.4, title="Distribution")
            fig_pie.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=300)
            st.plotly_chart(fig_pie, width="stretch")

if __name__ == "__main__":
    main()
