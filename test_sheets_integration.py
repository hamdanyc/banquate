"""
Quick test to verify Google Sheets integration works
"""
import pandas as pd
import sheets_loader

# Test configuration
SHEET_URL = "https://docs.google.com/spreadsheets/d/1twmu4Ktr9l_798eoeXkfcctWzs3u6BzYlpd8Q_cu0lY/edit?usp=sharing"
WORKSHEET_INDEX = 0

print("Testing Google Sheets Integration...")
print(f"Sheet URL: {SHEET_URL}")
print(f"Worksheet Index: {WORKSHEET_INDEX}")
print("-" * 60)

try:
    # Test URL parsing
    sheet_id = sheets_loader.get_sheet_id_from_url(SHEET_URL)
    print(f"✓ Sheet ID extracted: {sheet_id}")
    
    # Test data loading
    print("\nLoading data from Google Sheets...")
    df = sheets_loader.load_from_google_sheets(SHEET_URL, WORKSHEET_INDEX)
    
    print(f"✓ Data loaded successfully!")
    print(f"  - Rows: {len(df)}")
    print(f"  - Columns: {list(df.columns)}")
    
    # Check required columns
    required_columns = ['table_number', 'seat', 'name', 'menu', 'gp_id', 'gp_name']
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        print(f"✗ Missing columns: {missing}")
    else:
        print(f"✓ All required columns present")
    
    # Show sample data
    print("\nSample data (first 5 rows):")
    print(df.head())
    
    # Show statistics
    if not df.empty:
        total_tables = df['table_number'].nunique()
        total_guests = len(df)
        print(f"\n✓ Statistics:")
        print(f"  - Total guests: {total_guests}")
        print(f"  - Total tables: {total_tables}")
        
        if 'menu' in df.columns:
            menu_counts = df['menu'].value_counts()
            print(f"  - Menu breakdown:")
            for menu, count in menu_counts.items():
                print(f"    • {menu}: {count}")
    
    print("\n" + "=" * 60)
    print("✓ Google Sheets integration test PASSED!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Test FAILED: {e}")
    import traceback
    traceback.print_exc()
