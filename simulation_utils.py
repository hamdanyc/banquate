import pandas as pd

def simulate_table_addition(df, insert_after_ids):
    """
    Simulates adding new tables after specific table IDs.
    
    Args:
        df (pd.DataFrame): Current guest list data.
        insert_after_ids (list or int): List of table IDs after which to insert new tables.
                                        Can be a single int for backward compatibility.
        
    Returns:
        tuple: (simulated_dataframe, new_table_order_list, list_of_new_ids)
    """
    # Normalize input to list
    if isinstance(insert_after_ids, int):
        target_ids = [insert_after_ids]
    else:
        target_ids = list(insert_after_ids)
        
    # 1. Get max table ID from current data
    if not df.empty and 'table_number' in df.columns:
        current_max = df['table_number'].max()
    else:
        current_max = 0
        
    # Prepare to track new tables
    # We will generate IDs sequentially: max+1, max+2, ...
    next_id_start = int(current_max) + 1
    new_tables_info = [] # List of (new_id, target_id)
    
    for i, target in enumerate(target_ids):
        new_id = next_id_start + i
        new_tables_info.append({'new_id': new_id, 'target': target})
    
    generated_new_ids = [info['new_id'] for info in new_tables_info]
    
    # 2. Get current unique tables sorted
    if not df.empty and 'table_number' in df.columns:
        unique_tables = sorted(df['table_number'].unique())
        unique_tables = [int(t) for t in unique_tables if t != 0]
    else:
        unique_tables = []

    # 3. Create new order
    # Strategy: Iterate through original order. If current table matches a target, append it THEN append the new table(s).
    # Need to handle case where multiple insertions happen after same table? (Rare but possible: 7, 7 -> insert 2 tables after 7)
    # The logic below handles one insertion per target occurrence in the loop.
    # To handle multiple targets being the same ID, we should process targets as a map: {target_id: [new_id1, new_id2...]}
    
    from collections import defaultdict
    insertions_map = defaultdict(list)
    for info in new_tables_info:
        insertions_map[info['target']].append(info['new_id'])
        
    new_order = []
    
    # Handle case where list is empty
    if not unique_tables:
        # Just append all new tables
        for new_id in generated_new_ids:
            new_order.append(new_id)
    else:
        # Check for insertions before everything (target=0 usually, or just logic)
        if 0 in insertions_map:
             new_order.extend(insertions_map[0])
             
        for t in unique_tables:
            new_order.append(t)
            if t in insertions_map:
                new_order.extend(insertions_map[t])
        
        # Check for insertions that didn't match any existing table (e.g. target > max, or simply not found)
        # We should append them at the end.
        processed_targets = set(unique_tables)
        if 0 in insertions_map: processed_targets.add(0)
        
        for target, new_ids in insertions_map.items():
            if target not in processed_targets:
                new_order.extend(new_ids)

    # 4. Create rows for new tables
    new_rows = []
    for new_id in generated_new_ids:
        new_rows.append({
            'table_number': new_id,
            'name': 'Reserved (Simulated)',
            'gp_name': 'SIMULATION',
            'menu': 'Reserve',
            'seat': 1
        })
    
    # 5. Concat to df
    if new_rows:
        new_rows_df = pd.DataFrame(new_rows)
        sim_df = pd.concat([df, new_rows_df], ignore_index=True)
    else:
        sim_df = df.copy()
    
    return sim_df, new_order, generated_new_ids
