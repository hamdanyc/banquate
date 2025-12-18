"""
Google Sheets data loader for banquet seating application.
Provides functions to load and save guest data from/to Google Sheets.
Supports both Streamlit secrets (local) and environment variables (Posit Connect).
"""

import pandas as pd
import streamlit as st
import re
import os
import json


def get_credentials():
    """
    Get Google Service Account credentials from Streamlit secrets or environment variables.
    
    Priority:
    1. Streamlit secrets (st.secrets['gcp_service_account'])
    2. Environment variable GCP_SERVICE_ACCOUNT (JSON string)
    3. Individual environment variables (GCP_TYPE, GCP_PROJECT_ID, etc.)
    
    Returns:
        dict: Service account credentials dictionary, or None if not available
    """
    # Try Streamlit secrets first (for local development)
    # if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
    #    return dict(st.secrets['gcp_service_account'])
    
    # Try environment variable with full JSON (for Posit Connect - Option 1)
    gcp_json = os.environ.get('GCP_SERVICE_ACCOUNT')
    if gcp_json:
        try:
            return json.loads(gcp_json)
        except json.JSONDecodeError as e:
            st.warning(f"Failed to parse GCP_SERVICE_ACCOUNT environment variable: {e}")
    
    # Try individual environment variables (for Posit Connect - Option 2)
    env_creds = {
        'type': os.environ.get('GCP_TYPE'),
        'project_id': os.environ.get('GCP_PROJECT_ID'),
        'private_key_id': os.environ.get('GCP_PRIVATE_KEY_ID'),
        'private_key': os.environ.get('GCP_PRIVATE_KEY'),
        'client_email': os.environ.get('GCP_CLIENT_EMAIL'),
        'client_id': os.environ.get('GCP_CLIENT_ID'),
        'auth_uri': os.environ.get('GCP_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
        'token_uri': os.environ.get('GCP_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
        'auth_provider_x509_cert_url': os.environ.get('GCP_AUTH_PROVIDER_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
        'client_x509_cert_url': os.environ.get('GCP_CLIENT_CERT_URL'),
    }
    
    # Check if all required fields are present
    required_fields = ['type', 'project_id', 'private_key', 'client_email']
    if all(env_creds.get(field) for field in required_fields):
        # Fix private key formatting (replace literal \n with actual newlines)
        if env_creds['private_key']:
            env_creds['private_key'] = env_creds['private_key'].replace('\\n', '\n')
        return env_creds
    
    # No credentials found
    return None


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
        
        # Try to get credentials
        credentials_dict = get_credentials()
        
        gc = None
        if credentials_dict:
            # Use service account credentials
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
                f"2. Service account credentials are configured in Streamlit secrets or environment variables.\n"
                f"Original error: {error_msg}"
            )
        elif "404" in error_msg or "Not Found" in error_msg:
            raise Exception(
                f"Google Sheet not found. Please check the URL is correct.\n"
                f"Original error: {error_msg}"
            )
        elif "No secrets found" in error_msg:
            raise Exception(
                f"No credentials found. For Posit Connect deployment:\n"
                f"1. Set environment variable GCP_SERVICE_ACCOUNT with full JSON credentials, OR\n"
                f"2. Set individual environment variables (GCP_TYPE, GCP_PROJECT_ID, GCP_PRIVATE_KEY, GCP_CLIENT_EMAIL, etc.)\n"
                f"See POSIT_CONNECT_DEPLOYMENT.md for detailed instructions.\n"
                f"Original error: {error_msg}"
            )
        else:
            raise Exception(f"Failed to load data from Google Sheets: {error_msg}")


def save_to_google_sheets(df, sheet_url, worksheet_index=0):
    """
    Save DataFrame back to Google Sheets.
    Requires service account credentials configured in Streamlit secrets or environment variables.
    
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
        
        # Get credentials
        credentials_dict = get_credentials()
        
        if not credentials_dict:
            raise ValueError(
                "Google Sheets write access requires service account credentials. "
                "Please configure credentials in Streamlit secrets or environment variables. "
                "See POSIT_CONNECT_DEPLOYMENT.md for instructions."
            )
        
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
