import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import pdf_gen
import dashboard_gen

# --- Configuration ---
DEFAULT_ROWS = 7
DEFAULT_COLS = 9
DATA_FILE = "data/guest_list.csv"

# --- Component Definition ---
import os
parent_dir = os.path.dirname(os.path.abspath(__file__))
component_path = os.path.join(parent_dir, "grid_component")
print(f"Loading component from: {component_path}")

# Declare the component
# Use a different name to avoid potential caching issues with the previous name
custom_grid = components.declare_component("banquet_grid", path=component_path)

# --- Data Management ---
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["table_number", "seat", "name", "menu", "gp_id", "gp_name"])
    try:
        df = pd.read_csv(DATA_FILE)
        if 'table_number' in df.columns:
            df['table_number'] = pd.to_numeric(df['table_number'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def save_data(df):
    try:
        df.to_csv(DATA_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

# --- Business Logic ---
def get_table_id(r, c, cols):
    """Calculates table number based on grid position (1-based index)."""
    return (r * cols) + (c + 1)

def get_table_id_oddeven(r, c, cols):
    """Odd numbers on left, Even on right per row."""
    start_num = (r * cols) + 1
    end_num = (r + 1) * cols
    row_nums = range(start_num, end_num + 1)
    odds = [n for n in row_nums if n % 2 != 0]
    evens = [n for n in row_nums if n % 2 == 0]
    sorted_nums = odds + evens
    return sorted_nums[c]

def swap_tables(df, t1_id, t2_id):
    """Swaps the occupants of two tables by updating table_number."""
    t1_rows = df[df['table_number'] == t1_id].index
    t2_rows = df[df['table_number'] == t2_id].index
    
    TEMP_ID = -999
    
    df.loc[t1_rows, 'table_number'] = TEMP_ID
    df.loc[t2_rows, 'table_number'] = t1_id
    df.loc[df['table_number'] == TEMP_ID, 'table_number'] = t2_id
    
    return df

# --- Main App ---
def main():
    st.set_page_config(layout="wide", page_title="Banquet Seating")
    
    # State initialization
    if 'rows' not in st.session_state:
        st.session_state.rows = DEFAULT_ROWS
    if 'cols' not in st.session_state:
        st.session_state.cols = DEFAULT_COLS

    if 'mode' not in st.session_state:
        st.session_state.mode = 'Grid'
    if 'grid_mode' not in st.session_state:
        st.session_state.grid_mode = 'Move'
    if 'edit_target' not in st.session_state:
        st.session_state.edit_target = None
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'grid_component_key' not in st.session_state:
        st.session_state.grid_component_key = 0
        
    # Header
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("🍽️ Majlis Makan Malam RAFOC 2025")
        st.write("WTC 14 Dis 2025")
    
    # Custom CSS - Minimal for ensuring layout consistency if needed
    st.markdown("""
    <style>
    /* Report Table Styling */
    .dataframe {
        font-size: 14px;
        width: 100%;
    }
    .stButton button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

    df = load_data()

    # Sidebar
    st.sidebar.title("Navigation")
    
    # Grid Config
    with st.sidebar.expander("Grid Settings", expanded=False):
        new_rows = st.number_input("Rows", min_value=1, max_value=20, value=st.session_state.rows)
        new_cols = st.number_input("Columns", min_value=1, max_value=20, value=st.session_state.cols)
        
        if new_rows != st.session_state.rows or new_cols != st.session_state.cols:
            st.session_state.rows = new_rows
            st.session_state.cols = new_cols
            st.rerun()

    # Layout & Data Tools
    with st.sidebar.expander("Layout & Tools", expanded=False):
        layout_view = st.radio("Grid Numbering", ["Sequential", "Odd/Even"], index=0, key="layout_radio")
        
        st.markdown("---")
        st.caption("Reassign Table Numbers")
        if st.button("⚠ Reassign to Odd/Even"):
            # Transformation Logic
            id_map = {}
            c_rows = st.session_state.rows
            c_cols = st.session_state.cols
            
            for r in range(c_rows):
                for c in range(c_cols):
                    old_id = get_table_id(r, c, c_cols)
                    new_id = get_table_id_oddeven(r, c, c_cols)
                    id_map[old_id] = new_id
            
            if not df.empty:
                new_df = df.copy()
                # Map using the dictionary; values not in map are unchanged (using map with fillna/combine or replace)
                # Safest for integer mapping with replace is usually replace(dict).
                new_df['table_number'] = new_df['table_number'].replace(id_map)
                
                if save_data(new_df):
                    st.success("Renumbering Complete!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Failed to save data.")
            
    view_mode = st.sidebar.radio("View", ["Grid Layout", "Guest List"], index=0 if st.session_state.mode == 'Grid' else 1)
    
    # Reports
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Reports & Exports")
    if not df.empty:
        try:
            pdf2 = pdf_gen.generate_guest_list_by_table(df)
            st.sidebar.download_button("Guest List (By Table)", data=pdf2, file_name="guest_list_by_table.pdf", mime="application/pdf")
            
            pdf1 = pdf_gen.generate_guest_list_sorted(df)
            st.sidebar.download_button("Guest List (A-Z)", data=pdf1, file_name="guest_list_az.pdf", mime="application/pdf")
            
            pdf3 = pdf_gen.generate_table_summary(df)
            st.sidebar.download_button("Table Summary", data=pdf3, file_name="table_summary.pdf", mime="application/pdf")

            # Dashboard Export
            st.sidebar.markdown("---")
            dash_html = dashboard_gen.generate_dashboard_html(df, st.session_state.rows, st.session_state.cols)
            st.sidebar.download_button(
                "Export Dashboard (HTML)", 
                data=dash_html, 
                file_name="banquet_dashboard.html", 
                mime="text/html"
            )
        except Exception as e:
            st.sidebar.error(f"Error generating PDF: {e}")

    # CSV Exports
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 CSV Exports")
    if not df.empty:
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')

        menu_types = ["Ayam", "Daging", "Ikan", "Vegetarian"]
        for m_type in menu_types:
            # Filter by menu type (case insensitive)
            # Ensure menu column is string and handle NaNs
            mask = df['menu'].fillna('').astype(str).str.contains(m_type, case=False)
            sub_df = df[mask].copy()
            
            # Select specific columns
            if not sub_df.empty:
                # Sort by table and seat
                sub_df = sub_df.sort_values(by=["table_number", "seat"])
                export_df = sub_df[["table_number", "seat", "name"]]
                csv = convert_df(export_df)
                st.sidebar.download_button(
                    label=f"Export {m_type} (CSV)",
                    data=csv,
                    file_name=f"guest_list_{m_type.lower()}.csv",
                    mime="text/csv",
                )

    # --- LIST View ---
    if view_mode == "Guest List":
        st.subheader("Senarai Tetamu")
        
        # Filters
        c_filter1, c_filter2 = st.columns([1, 2])
        with c_filter1:
            tables = sorted(df['table_number'].unique())
            selected_table = st.selectbox("Saring Mengikut Meja:", ["Semua"] + [str(t) for t in tables])
        
        with c_filter2:
            search = st.text_input("Carian (Nama)", value=st.session_state.search_query)
        
        filtered_df = df.copy()
        
        if selected_table != "Semua":
            filtered_df = filtered_df[filtered_df['table_number'].astype(str) == selected_table]
        
        if search:
            filtered_df = filtered_df[filtered_df['name'].str.contains(search, case=False, na=False)]
        
        filtered_df = filtered_df.sort_values(by=["table_number", "seat"])
        
        display_df = filtered_df[["table_number", "seat", "name", "menu", "gp_name"]].copy()
        display_df.columns = ["Meja", "Seat", "Nama", "Menu", "Kluster"]
        
        display_df = display_df.reset_index(drop=True)
        display_df.index = display_df.index + 1
        
        st.dataframe(display_df, use_container_width=True)
        
    # --- GRID View ---
    else:
        st.session_state.mode = "Grid" 
        
        # Grid Controls
        c1, c2, c3 = st.columns([2, 5, 2])
        with c1:
            g_mode = st.radio("Grid Mode", ["Move", "Edit"], horizontal=True, key="grid_mode_radio")
            if g_mode != st.session_state.grid_mode:
                st.session_state.grid_mode = g_mode
                st.session_state.grid_component_key += 1 # Force refresh when mode changes
                st.rerun()
        
        with c2:
            if st.session_state.grid_mode == "Move":
                st.info("Drag and drop tables to swap them.")
            else:
                if st.session_state.edit_target:
                    st.success(f"Editing Table {st.session_state.edit_target}")
                else:
                    st.info("Click a table to edit details.")
        
        with c3:
            if st.button("Refresh Data"):
                st.cache_data.clear()
                st.session_state.grid_component_key += 1
                st.rerun()

        # Edit Form
        if st.session_state.grid_mode == "Edit" and st.session_state.edit_target is not None:
            display_tid = st.session_state.edit_target
            
            # Resolve Data ID
            # Re-implement helper logic localized here or move helper to outer scope (preferred to use local calc for robust scope)
            if layout_view == "Odd/Even":
                 # display_tid is 1-based sequential
                 idx = display_tid - 1
                 r = idx // st.session_state.cols
                 c = idx % st.session_state.cols
                 data_tid = get_table_id_oddeven(r, c, st.session_state.cols)
            else:
                 data_tid = display_tid

            with st.expander(f"📝 Edit Table {display_tid}", expanded=True):
                if display_tid != data_tid:
                    st.caption(f"mapped to Internal Data Table ID: {data_tid}")
                    
                table_df = df[df['table_number'] == data_tid].copy()
                
                current_group = ""
                if not table_df.empty:
                    current_group = table_df.iloc[0]['gp_name'] if 'gp_name' in table_df.columns else ""
                
                new_group_name = st.text_input("Group Name", value=current_group)
                
                edit_cols = ["seat", "name", "menu"]
                for col in edit_cols:
                    if col not in table_df.columns:
                        table_df[col] = ""
                
                edited_guests = st.data_editor(
                    table_df[edit_cols],
                    num_rows="dynamic",
                    key=f"editor_{display_tid}" # Keep display ID for key uniqueness
                )
                
                if st.button("Save Changes"):
                    df = df[df['table_number'] != data_tid]
                    if not edited_guests.empty:
                        edited_guests['table_number'] = data_tid
                        edited_guests['gp_name'] = new_group_name
                        edited_guests['gp_id'] = 0 
                        df = pd.concat([df, edited_guests], ignore_index=True)
                    
                    if save_data(df):
                        st.success("Saved!")
                        st.session_state.grid_component_key += 1 # Refresh grid to show new group name/count
                        st.rerun()

        # Prepare Data for Custom Grid
        table_map = {}
        grouped = df.groupby('table_number')
        for tid, group in grouped:
            table_map[tid] = {
                'occupied': True,
                'group': str(group.iloc[0]['gp_name']) if 'gp_name' in group.columns and pd.notna(group.iloc[0]['gp_name']) else 'Unknown',
                'count': len(group)
            }
            
        current_rows = st.session_state.rows
        current_cols = st.session_state.cols
        
        # Helper to map Display ID -> Data ID based entirely on current view mode
        # We need to find the (r,c) for a given Display ID (Sequential), then calculate the Data ID (Odd/Even or Seq)
        def get_data_id_from_display_id(display_id, rows, cols, mode):
            if mode != "Odd/Even":
                return display_id
            
            # Reverse engineer (r,c) from sequential ID
            # ID = (r * cols) + (c + 1)
            # ID - 1 = r * cols + c
            idx = display_id - 1
            r = idx // cols
            c = idx % cols
            
            return get_table_id_oddeven(r, c, cols)

        grid_data = []
        for r in range(current_rows):
            for c in range(current_cols):
                display_id = get_table_id(r, c, current_cols)
                
                if layout_view == "Odd/Even":
                    data_id = get_table_id_oddeven(r, c, current_cols)
                else:
                    data_id = display_id
                
                data = table_map.get(data_id, {'occupied': False, 'group': '', 'count': 0})
                
                # Send DISPLAY ID to the frontend component
                grid_data.append({
                    'id': display_id,
                    'occupied': data['occupied'],
                    'group': data['group'],
                    'count': data['count']
                })

        # Render Custom Component
        event = custom_grid(
            tables=grid_data,
            rows=current_rows,
            cols=current_cols,
            mode=st.session_state.grid_mode,
            selectedId=st.session_state.edit_target if st.session_state.grid_mode == "Edit" else None,
            key=f"grid_{st.session_state.grid_component_key}"
        )

        if event:
            if event.get("action") == "swap":
                d_t1 = event.get("fromId")
                d_t2 = event.get("toId")
                
                if d_t1 and d_t2 and d_t1 != d_t2:
                    # Convert Display IDs -> Data IDs
                    t1 = get_data_id_from_display_id(d_t1, current_rows, current_cols, layout_view)
                    t2 = get_data_id_from_display_id(d_t2, current_rows, current_cols, layout_view)
                    
                    new_df = swap_tables(df, t1, t2)
                    save_data(new_df)
                    st.toast(f"Swapped Table {d_t1} ({t1}) and {d_t2} ({t2})")
                    st.session_state.grid_component_key += 1
                    st.rerun()
            
            elif event.get("action") == "edit":
                d_tid = event.get("tableId")
                st.session_state.edit_target = d_tid
                st.rerun()

if __name__ == "__main__":
    main()
