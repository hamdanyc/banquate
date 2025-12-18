"""
Google Sheets data loader for banquet seating application.
Provides functions to load and save guest data from/to Google Sheets.
"""

import pandas as pd
import streamlit as st
import re


def get_sheet_id_from_url(url):
    """
    Extract the Google Sheet ID from a URL.
    
    Args:
        url: Google Sheets URL
        
    Returns:
        Sheet ID string
        
    Raises:
        ValueError: If URL format is invalid
    """
    # Pattern: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit...
    pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
    match = re.search(pattern, url)
    
    if not match:
        raise ValueError(f"Invalid Google Sheets URL: {url}")
    
    return match.group(1)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_from_google_sheets(sheet_url, worksheet_index=0):
    """
    Load data from Google Sheets into a pandas DataFrame.
    Uses gspread for authenticated or public access.
    
    Args:
        sheet_url: Full URL to the Google Sheet
        worksheet_index: Index of the worksheet to load (default: 0 for first sheet)
        
    Returns:
        pandas DataFrame with guest data
        
    Raises:
        Exception: If loading fails
    """
    try:
        import gspread
        from gspread_dataframe import get_as_dataframe
        
        # Extract sheet ID from URL
        sheet_id = get_sheet_id_from_url(sheet_url)
        
        # Try to use service account credentials if available
        gc = None
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            credentials_dict = dict(st.secrets['gcp_service_account'])
            gc = gspread.service_account_from_dict(credentials_dict)
        else:
            # For public sheets, use anonymous access
            # This requires the sheet to be shared with "Anyone with the link can view"
            gc = gspread.auth.Client(auth=None)
        
        # Open the spreadsheet
        spreadsheet = gc.open_by_key(sheet_id)
        
        # Get the worksheet
        worksheet = spreadsheet.get_worksheet(worksheet_index)
        
        # Get all values as list of lists
        values = worksheet.get_all_values()
        
        if not values:
            raise ValueError("Sheet is empty")
        
        # First row is headers
        headers = values[0]
        data_rows = values[1:]
        
        # Create DataFrame
        df = pd.DataFrame(data_rows, columns=headers)
        
        # Ensure required columns exist
        required_columns = ['table_number', 'seat', 'name', 'menu', 'gp_id', 'gp_name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Convert data types
        df['table_number'] = pd.to_numeric(df['table_number'], errors='coerce')
        df['seat'] = pd.to_numeric(df['seat'], errors='coerce')
        df['gp_id'] = pd.to_numeric(df['gp_id'], errors='coerce')
        
        # Fill NaN values
        df['name'] = df['name'].fillna('')
        df['menu'] = df['menu'].fillna('')
        df['gp_name'] = df['gp_name'].fillna('')
        
        # Remove rows with invalid table numbers
        df = df[df['table_number'].notna()]
        
        return df
        
    except ImportError:
        raise Exception(
            "gspread is required for Google Sheets access. "
            "Please install: pip install gspread gspread-dataframe"
        )
    except Exception as e:
        # Provide helpful error messages
        error_msg = str(e)
        if "403" in error_msg or "Forbidden" in error_msg:
            raise Exception(
                f"Access denied to Google Sheet. Please ensure:\n"
                f"1. The sheet is shared with 'Anyone with the link can view', OR\n"
                f"2. Service account credentials are configured in Streamlit secrets.\n"
                f"Original error: {error_msg}"
            )
        elif "404" in error_msg or "Not Found" in error_msg:
            raise Exception(
                f"Google Sheet not found. Please check the URL is correct.\n"
                f"Original error: {error_msg}"
            )
        else:
            raise Exception(f"Failed to load data from Google Sheets: {error_msg}")


def save_to_google_sheets(df, sheet_url, worksheet_index=0):
    """
    Save DataFrame back to Google Sheets.
    Requires service account credentials configured in Streamlit secrets.
    
    Args:
        df: pandas DataFrame to save
        sheet_url: Full URL to the Google Sheet
        worksheet_index: Index of the worksheet to update (default: 0)
        
    Returns:
        True if successful
        
    Raises:
        Exception: If saving fails or credentials not configured
    """
    try:
        import gspread
        from gspread_dataframe import set_with_dataframe
        
        # Check for credentials in Streamlit secrets
        if not hasattr(st, 'secrets') or 'gcp_service_account' not in st.secrets:
            raise ValueError(
                "Google Sheets write access requires service account credentials. "
                "Please add 'gcp_service_account' to your Streamlit secrets (.streamlit/secrets.toml)."
            )
        
        credentials_dict = dict(st.secrets['gcp_service_account'])
        
        # Extract sheet ID
        sheet_id = get_sheet_id_from_url(sheet_url)
        
        # Create authenticated client
        gc = gspread.service_account_from_dict(credentials_dict)
        
        # Open the spreadsheet
        spreadsheet = gc.open_by_key(sheet_id)
        
        # Get the worksheet
        worksheet = spreadsheet.get_worksheet(worksheet_index)
        
        # Clear existing data
        worksheet.clear()
        
        # Write DataFrame to sheet
        set_with_dataframe(worksheet, df, include_index=False, include_column_header=True)
        
        # Clear cache to force reload on next access
        load_from_google_sheets.clear()
        
        return True
        
    except ImportError:
        raise Exception(
            "gspread and gspread-dataframe are required for write access. "
            "Please install: pip install gspread gspread-dataframe"
        )
    except Exception as e:
        raise Exception(f"Failed to save data to Google Sheets: {str(e)}")
