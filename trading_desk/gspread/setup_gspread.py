import datetime
import os

## gspread
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def init_gspread(session_name:str,
                 tmux_session_name:str):
    scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    ]

    json_file_name = os.getenv("GSPREAD_JSON_FILE_NAME")    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    json_file_dir = os.path.join(BASE_DIR, "gspread_key", json_file_name)

    spreadsheet_url = os.getenv("SPREADSHEET_URL")

    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_dir, scope)
    gc = gspread.authorize(credentials)
    doc = gc.open_by_url(spreadsheet_url)

    # Create a new sheet
    if session_name not in [ws.title for ws in doc.worksheets()]:
        doc.add_worksheet(title=session_name,
                          rows=100, 
                          cols=20)
    else:
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        worksheet_title = f"{session_name}_new_{timestamp}"
        doc.add_worksheet(title=worksheet_title,
                          rows=100, 
                          cols=20)

    ws = doc.worksheet(session_name)

    return ws
