import pandas as pd
import textwrap
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm

def generate_cards_from_public_gsheet(sheet_url, output_pdf, logo_path='logo/rafoc.png'):
    # Clean the URL to get the direct CSV export link
    base_url = sheet_url.split('/edit')[0]
    csv_url = f"{base_url}/export?format=csv"
    
    print(f"Fetching data from: {csv_url}")
    
    try:
        df = pd.read_csv(csv_url)
    except Exception as e:
        print(f"Error downloading sheet: {e}")
        return

    # 6 cards per A4 page (2 columns x 3 rows)
    width = 90 * mm
    side_height = 48 * mm  # Each face is 48mm
    total_height = side_height * 2 
    
    c = canvas.Canvas(output_pdf, pagesize=A4)
    page_width, page_height = A4
    
    # Layout margins
    margin_x = (page_width - (width * 2 + 10*mm)) / 2
    margin_y = (page_height - (total_height * 3 + 10*mm)) / 2
    gap_x, gap_y = 10 * mm, 5 * mm
    
    curr_x = margin_x
    curr_y = page_height - margin_y - total_height

    color_map = {
        "Daging": colors.white, 
        "Ayam": colors.brown, 
        "Ikan": colors.yellow, 
        "Vegetarian": colors.green
    }

    for index, row in df.iterrows():
        # --- CARD OUTLINE ---
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.2)
        c.rect(curr_x, curr_y, width, total_height)
        
        # Fold Line (Dashed)
        c.setDash(1, 2)
        c.line(curr_x, curr_y + side_height, curr_x + width, curr_y + side_height)
        c.setDash([]) 

        # --- SECTION 1: BACK FACE (Flipped 180°) ---
        c.saveState()
        # Origin is now at the center of the top half
        c.translate(curr_x + width/2, curr_y + side_height + (side_height/2))
        c.rotate(180)
        
        # Logo: Centered vertically in this section (well away from the fold line)
        if os.path.exists(logo_path):
            logo_w = 25 * mm
            logo_h = 15 * mm
            # Placing it slightly above center (closer to the paper edge)
            # In flipped space, y=0 is center, y=24 is fold, y=-24 is edge.
            c.drawImage(logo_path, -logo_w/2, 2 * mm, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
        
        # Title: Placed below the logo
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(0, -12 * mm, "ANNUAL DINNER 2025")
        c.restoreState()

        # --- SECTION 2: GUEST FACE (Upright) ---
        # 1. Menu Indicator Rectangle (Top Right)
        meal_type = str(row.get('menu', 'Daging'))
        c.setFillColor(color_map.get(meal_type, colors.white))
        c.rect(curr_x + width - 15*mm, curr_y + side_height - 10*mm, 10*mm, 5*mm, fill=1, stroke=1)

        # 2. Guest Name (Wrapped)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 12)
        name = str(row.get('name', '')).upper()
        wrapped_name = textwrap.wrap(name, width=22)
        name_y = curr_y + 25 * mm
        for line in wrapped_name[:2]:
            c.drawCentredString(curr_x + width/2, name_y, line)
            name_y -= 5.5 * mm

        # 3. Table and Seat
        c.setFont("Helvetica", 10)
        table_info = f"Meja: {row.get('table_number', '')} | {row.get('seat', '')}"
        c.drawCentredString(curr_x + width/2, curr_y + 11 * mm, table_info)
        
        # 4. Group Name
        c.setFont("Helvetica-Oblique", 7)
        c.drawCentredString(curr_x + width/2, curr_y + 5 * mm, f"{row.get('gp_name', '')}")

        # --- GRID POSITIONING ---
        curr_x += width + gap_x
        if curr_x + width > page_width - margin_x:
            curr_x = margin_x
            curr_y -= (total_height + gap_y)
            
        if curr_y < margin_y:
            c.showPage()
            curr_x = margin_x
            curr_y = page_height - margin_y - total_height

    c.save()
    print(f"Cards saved to {output_pdf}")

# Execution
PUBLIC_URL = "https://docs.google.com/spreadsheets/d/1twmu4Ktr9l_798eoeXkfcctWzs3u6BzYlpd8Q_cu0lY/edit?usp=sharing"
generate_cards_from_public_gsheet(PUBLIC_URL, "Menu_Cards.pdf")