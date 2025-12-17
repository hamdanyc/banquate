from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
import pandas as pd
from datetime import datetime

def build_header_main(elements, styles):
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=10,
        textColor=colors.black
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=20,
        textColor=colors.black
    )
    
    elements.append(Paragraph("Majlis Makan Malam RAFOC `25", title_style))
    current_time = datetime.now().strftime("%d-%m-%Y %H:%M")
    elements.append(Paragraph(f"Berakhir pada: {current_time}", subtitle_style))
    elements.append(Spacer(1, 10))

def build_header_summary(elements, styles):
    title_style = ParagraphStyle(
        'SummaryTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=0,
        textColor=colors.black,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'SummarySubtitle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=20,
        textColor=colors.black
    )
    
    elements.append(Paragraph("Tables Summary", title_style))
    elements.append(Spacer(1, 10))
    current_time = datetime.now().strftime("%d-%m-%Y %H:%M")
    elements.append(Paragraph(f"Berakhir pada: {current_time}", subtitle_style))
    elements.append(Spacer(1, 10))

def generate_guest_list_sorted(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    build_header_main(elements, styles)
    elements.append(Paragraph("Guest List (By Name)", styles['Heading2']))
    elements.append(Spacer(1, 12))

    sorted_df = df.sort_values(by="name", key=lambda col: col.str.lower())
    
    data = [["No", "Nama", "Meja", "Kluster"]]
    for i, row in enumerate(sorted_df.itertuples(), 1):
        name = row.name if pd.notna(row.name) else ""
        table = str(row.table_number) if pd.notna(row.table_number) else ""
        group = row.gp_name if pd.notna(row.gp_name) else ""
        data.append([str(i), name, table, group])

    t = Table(data, colWidths=[30, 250, 50, 150])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_guest_list_by_table(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    build_header_main(elements, styles)
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=6,
        spaceBefore=12,
        textColor=colors.black
    )

    if 'table_number' in df.columns:
        df['table_number'] = pd.to_numeric(df['table_number'], errors='coerce').fillna(0)
    
    unique_tables = sorted(df['table_number'].unique())

    for table_num in unique_tables:
        if table_num == 0: continue
        
        table_df = df[df['table_number'] == table_num].sort_values(by='seat')
        if table_df.empty: continue

        group_name = table_df.iloc[0]['gp_name'] if 'gp_name' in table_df.columns and pd.notna(table_df.iloc[0]['gp_name']) else ""
        
        block_elements = []
        header_text = f"Meja: {int(table_num)} | {group_name}"
        block_elements.append(Paragraph(header_text, table_header_style))
        
        data = [["Siri", "Tetamu", "Menu"]]
        for i, row in enumerate(table_df.itertuples(), 1):
            name = row.name if pd.notna(row.name) else ""
            menu = row.menu if pd.notna(row.menu) else ""
            data.append([str(i), name, menu])
            
        t = Table(data, colWidths=[40, 350, 100], hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        block_elements.append(t)
        block_elements.append(Spacer(1, 15))
        elements.append(KeepTogether(block_elements))

    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_table_summary(df, table_order=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    build_header_summary(elements, styles)

    # Columns
    headers = ["Table\nNumber", "Table\nName", "Total\nGuests", "Reserved", "Daging", "Ayam", "Ikan", "Vegetarian", "Adjusted\nTotal"]
    data = [headers]

    if 'table_number' in df.columns:
        df['table_number'] = pd.to_numeric(df['table_number'], errors='coerce').fillna(0)
    
    if table_order is not None:
        # Use provided order, filtering out 0 if present or ensuring it's valid
        unique_tables = [t for t in table_order if t != 0]
    else:
        unique_tables = sorted(df['table_number'].unique())
    
    # Init Totals
    sum_total_guests = 0
    sum_reserved = 0
    sum_daging = 0
    sum_ayam = 0
    sum_ikan = 0
    sum_vege = 0
    sum_adjusted = 0

    for table_num in unique_tables:
        if table_num == 0: continue
        
        table_df = df[df['table_number'] == table_num]
        
        group_name = table_df.iloc[0]['gp_name'] if 'gp_name' in table_df.columns and pd.notna(table_df.iloc[0]['gp_name']) else ""
        
        # Menu Counts
        menus = table_df['menu'].astype(str).str.lower()
        daging = menus.str.contains('daging').sum()
        ayam = menus.str.contains('ayam').sum()
        ikan = menus.str.contains('ikan').sum()
        vege = menus.str.contains('vege').sum()
        
        # Reserved Logic: 
        # Check name or gp_name for "simpanan", "reserve", "vacant"
        # Also check if menu is "reserve" (seen in data)
        names = table_df['name'].astype(str).str.lower()
        gp_names = table_df['gp_name'].astype(str).str.lower()
        
        # Row-wise reserve check
        is_reserved = (
            names.str.contains('simpanan') | 
            names.str.contains('reserve') | 
            names.str.contains('vacant') | 
            gp_names.str.contains('simpanan') | # If group is simpanan, all rows are reserved? Likely yes.
            gp_names.str.contains('reserve') |
            menus.str.contains('reserve')
        )
        reserved_count = is_reserved.sum()
        
        total_guests = len(table_df)
        adjusted_total = total_guests - reserved_count
        
        # Accumulate
        sum_total_guests += total_guests
        sum_reserved += reserved_count
        sum_daging += daging
        sum_ayam += ayam
        sum_ikan += ikan
        sum_vege += vege
        sum_adjusted += adjusted_total

        row = [
            str(int(table_num)),
            group_name,
            str(total_guests),
            str(reserved_count),
            str(daging),
            str(ayam),
            str(ikan),
            str(vege),
            str(adjusted_total)
        ]
        data.append(row)

    # ADD TOTAL ROW
    total_row = [
        "Total",
        "", # Table Name empty
        str(sum_total_guests),
        str(sum_reserved),
        str(sum_daging),
        str(sum_ayam),
        str(sum_ikan),
        str(sum_vege),
        str(sum_adjusted)
    ]
    data.append(total_row)

    # Styling
    t = Table(data, colWidths=[45, 120, 45, 45, 45, 45, 45, 55, 50])
    
    # Base Style
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ]
    
    # Total Row Style (Last Row)
    # Make it bold, maybe different background?
    style_cmds.append(('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'))
    
    t.setStyle(TableStyle(style_cmds))
    
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_floor_plan_layout(df, table_order, rows, cols):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'FPTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=10,
        textColor=colors.black,
        alignment=1 # CENTER
    )
    
    elements.append(Paragraph("Floor Plan Layout Simulation", title_style))
    elements.append(Spacer(1, 20))
    
    # Grid Data
    # 2D array of text
    grid_data = [['' for _ in range(cols)] for _ in range(rows)]
    
    for r in range(rows):
        for c in range(cols):
            # Calculate linear index based on row-major order
            idx = r * cols + c
            
            if idx < len(table_order):
                table_id = table_order[idx]
                
                # Get info
                if table_id == 0:
                     cell_text = ""
                else:
                    table_df = df[df['table_number'] == table_id]
                    count = len(table_df)
                    gp_name = ""
                    if not table_df.empty and 'gp_name' in table_df.columns:
                         # limit length
                         name = str(table_df.iloc[0]['gp_name'])
                         if len(name) > 15:
                             name = name[:12] + "..."
                         gp_name = name
                    
                    cell_text = f"T{table_id}\n{gp_name}\n({count} pax)"
                
                grid_data[r][c] = cell_text
    
    # Calculate cell size
    # A4 Landscape width ~840 points. Margins default to ~72. Usable ~700.
    # 700 / 9 cols ~ 77 pts.
    # Height ~595. Margins 72. Usable ~450.
    # 450 / 7 rows ~ 64 pts.
    
    col_width = 75
    row_height = 60
    
    t = Table(grid_data, colWidths=[col_width]*cols, rowHeights=[row_height]*rows)
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))
    
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    return buffer
