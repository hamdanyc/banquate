import streamlit as st
import pandas as pd
import os
import pdf_gen

# --- Configuration ---
DEFAULT_ROWS = 7
DEFAULT_COLS = 9
DATA_FILE = "data/guest_list.csv"

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
        
    if 'move_source' not in st.session_state:
        st.session_state.move_source = None
    if 'mode' not in st.session_state:
        st.session_state.mode = 'Grid' # Grid or List
    if 'grid_mode' not in st.session_state:
        st.session_state.grid_mode = 'Move' # Move or Edit
    if 'edit_target' not in st.session_state:
        st.session_state.edit_target = None
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""

    # Header
    c1, c2 = st.columns([3, 1])
    with c1:
        st.title("🍽️ Majlis Makan Malam RAFOC 2025")
        st.write("WTC 14 Dis 2025")
    
    # Custom CSS
    st.markdown("""
    <style>
    .table-box {
        border: 2px solid #ddd;
        border-radius: 8px;
        padding: 5px;
        text-align: center;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-bottom: 5px;
        background-color: #f0f0f0;
        color: #333;
    }
    .table-box.occupied {
        background-color: #00bcd4;
        color: white;
        border-color: #008ba3;
    }
    .table-box.vacant {
        background-color: #555; 
        color: #ddd;
    }
    .table-box.selected {
        border: 4px solid #ffeb3b; 
        transform: scale(1.05);
    }
    .table-id {
        font-weight: bold;
        font-size: 0.8em;
    }
    .group-name {
        font-weight: bold;
        font-size: 0.9em;
        line-height: 1.1;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    /* Report Table Styling */
    .dataframe {
        font-size: 14px;
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
            
    view_mode = st.sidebar.radio("View", ["Grid Layout", "Guest List"], index=0 if st.session_state.mode == 'Grid' else 1)
    
    # Reports
    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 PDF Reports")
    if not df.empty:
        try:
            pdf2 = pdf_gen.generate_guest_list_by_table(df)
            st.sidebar.download_button("Guest List (By Table)", data=pdf2, file_name="guest_list_by_table.pdf", mime="application/pdf")
            
            pdf1 = pdf_gen.generate_guest_list_sorted(df)
            st.sidebar.download_button("Guest List (A-Z)", data=pdf1, file_name="guest_list_az.pdf", mime="application/pdf")
            
            pdf3 = pdf_gen.generate_table_summary(df)
            st.sidebar.download_button("Table Summary", data=pdf3, file_name="table_summary.pdf", mime="application/pdf")
        except Exception as e:
            st.sidebar.error(f"Error generating PDF: {e}")

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
            st.session_state.grid_mode = g_mode
        
        with c2:
            if st.session_state.grid_mode == "Move":
                if st.session_state.move_source:
                    st.warning(f"Swap Mode: Select Target to swap Table {st.session_state.move_source}")
                else:
                    st.info("Select a table to move it.")
            else:
                if st.session_state.edit_target:
                    st.success(f"Editing Table {st.session_state.edit_target}")
                else:
                    st.info("Select a table to edit details.")
        
        with c3:
            if st.button("Refresh Data"):
                st.cache_data.clear()
                st.rerun()

        # Edit Form
        if st.session_state.grid_mode == "Edit" and st.session_state.edit_target is not None:
            tid = st.session_state.edit_target
            with st.expander(f"📝 Edit Table {tid}", expanded=True):
                table_df = df[df['table_number'] == tid].copy()
                
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
                    key=f"editor_{tid}"
                )
                
                if st.button("Save Changes"):
                    df = df[df['table_number'] != tid]
                    if not edited_guests.empty:
                        edited_guests['table_number'] = tid
                        edited_guests['gp_name'] = new_group_name
                        edited_guests['gp_id'] = 0 
                        df = pd.concat([df, edited_guests], ignore_index=True)
                    
                    if save_data(df):
                        st.success("Saved!")
                        st.rerun()

        # Render Grid
        table_map = {}
        grouped = df.groupby('table_number')
        for tid, group in grouped:
            table_map[tid] = {
                'occupied': True,
                'group': group.iloc[0]['gp_name'] if 'gp_name' in group.columns else 'Unknown',
                'count': len(group)
            }
            
        current_rows = st.session_state.rows
        current_cols = st.session_state.cols

        for r in range(current_rows):
            cols = st.columns(current_cols)
            for c in range(current_cols):
                tid = get_table_id(r, c, current_cols)
                data = table_map.get(tid, {'occupied': False, 'group': '', 'count': 0})
                
                is_selected = False
                if st.session_state.grid_mode == "Move" and st.session_state.move_source == tid:
                    is_selected = True
                if st.session_state.grid_mode == "Edit" and st.session_state.edit_target == tid:
                    is_selected = True

                css_class = "table-box " + ("occupied" if data['occupied'] else "vacant")
                if is_selected:
                    css_class += " selected"

                with cols[c]:
                    st.markdown(f"""
                    <div class="{css_class}">
                        <div class="table-id">{tid}</div>
                        <div class="group-name">{data['group'] if data['occupied'] else "Vacant"}</div>
                        <small>{data['count'] if data['occupied'] else ''}</small>
                    </div>
                    """, unsafe_allow_html=True)

                    btn_key = f"btn_{tid}"
                    label = "Action"
                    
                    if st.session_state.grid_mode == "Move":
                        if st.session_state.move_source == tid:
                            label = "Cancel"
                        elif st.session_state.move_source:
                            label = "Swap Here"
                        else:
                            label = "Move"
                        
                        if st.button(label, key=btn_key, use_container_width=True):
                            if label == "Move":
                                st.session_state.move_source = tid
                                st.rerun()
                            elif label == "Cancel":
                                st.session_state.move_source = None
                                st.rerun()
                            elif label == "Swap Here":
                                src = st.session_state.move_source
                                with st.spinner("Swapping..."):
                                    new_df = swap_tables(df, src, tid)
                                    save_data(new_df)
                                    st.session_state.move_source = None
                                    st.rerun()
                                    
                    elif st.session_state.grid_mode == "Edit":
                        label = "Edit"
                        type = "secondary"
                        if st.session_state.edit_target == tid:
                            type = "primary"
                        
                        if st.button(label, key=btn_key, type=type, use_container_width=True):
                            st.session_state.edit_target = tid
                            st.rerun()

if __name__ == "__main__":
    main()
