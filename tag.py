import pandas as pd
import textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
import os
# from PIL import Image

def generate_menu_cards(csv_file, output_pdf, logo_image='logo/rafoc.png'):
    # Load guest list
    df = pd.read_csv(csv_file)
    
    # 6 cards per A4 (2 columns x 3 rows)
    # Card size: 90mm width, 96mm total height (48mm front + 48mm back)
    width = 90 * mm
    side_height = 48 * mm 
    total_height = side_height * 2 
    
    c = canvas.Canvas(output_pdf, pagesize=A4)
    page_width, page_height = A4
    
    # Grid margins
    margin_x = (page_width - (width * 2 + 10*mm)) / 2
    margin_y = (page_height - (total_height * 3 + 10*mm)) / 2
    gap_x = 10 * mm
    gap_y = 5 * mm
    
    curr_x = margin_x
    curr_y = page_height - margin_y - total_height

    # Color Mapping for Menu
    color_map = {
        "Daging": colors.white,
        "Ayam": colors.brown,
        "Ikan": colors.yellow,
        "Vegetarian": colors.green
    }

    for index, row in df.iterrows():
        # 1. Draw Card Border and Fold Line
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.2)
        c.rect(curr_x, curr_y, width, total_height)
        c.setDash(1, 2)
        c.line(curr_x, curr_y + side_height, curr_x + width, curr_y + side_height)
        c.setDash([]) 

        # --- BACK SECTION (Top half of sheet, Flipped 180) ---
        c.saveState()
        c.translate(curr_x + width/2, curr_y + side_height + (side_height/2))
        c.rotate(180)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(0, 0, "ANNUAL DINNER 2025")
        c.restoreState()

        # --- FRONT SECTION (Bottom half of sheet, Upright) ---
        # 1. Logo at the TOP of the front face (near the fold)
        if os.path.exists(logo_image):
            logo_w = 25 * mm
            logo_h = 12 * mm
            # Placing it 5mm below the fold
            c.drawImage(logo_image, curr_x + (width - logo_w)/2, curr_y + side_height - 15*mm, 
                        width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')

        # 2. Menu Indicator (Small rectangle at top right of guest face)
        meal_type = row['menu']
        fill_color = color_map.get(meal_type, colors.white)
        c.setFillColor(fill_color)
        c.rect(curr_x + width - 15*mm, curr_y + side_height - 10*mm, 10*mm, 5*mm, fill=1, stroke=1)

        # 3. Guest Name (Wrapped for long names)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 12)
        name = str(row['name']).upper()
        wrapped_name = textwrap.wrap(name, width=22)
        name_y = curr_y + 22 * mm
        for line in wrapped_name[:2]: # Max 2 lines
            c.drawCentredString(curr_x + width/2, name_y, line)
            name_y -= 5 * mm

        # 4. Table and Seat Info
        c.setFont("Helvetica", 10)
        info_text = f"TABLE: {row['table_number']}    SEAT: {row['seat']}"
        c.drawCentredString(curr_x + width/2, curr_y + 10 * mm, info_text)
        
        # 5. Group/Company Name (Footer)
        c.setFont("Helvetica-Oblique", 7)
        c.drawCentredString(curr_x + width/2, curr_y + 4 * mm, f"{row['gp_name']}")

        # Move to next grid position
        curr_x += width + gap_x
        if curr_x + width > page_width - margin_x:
            curr_x = margin_x
            curr_y -= (total_height + gap_y)
            
        if curr_y < margin_y:
            c.showPage()
            curr_x = margin_x
            curr_y = page_height - margin_y - total_height

    c.save()
    print(f"Generated {output_pdf}")

# Create the PDF
generate_menu_cards('data/guest_list.csv', 'menu_card.pdf')