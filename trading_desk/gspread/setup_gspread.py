import datetime
import os
import string

## gspread
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def init_gspread(session_name:str):
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
        raise ValueError("Worksheet with the same name is existing")

    ws = doc.worksheet(session_name)

    return ws

def num_to_col(num):
    col = ""
    while num > 0:
        num, rem = divmod(num - 1, 26)
        col = chr(rem + ord('A')) + col
    return col

def setup_worksheet_format(worksheet,
                           strategy_name:str,
                           init_capital:float,
                           traded_assets:List[str],
                           tmux_session_name:str):
    # Alias
    CELL_CAPITAL = "C2"      

    # Session info
    worksheet.update([["strategy", strategy_name]], "B2:C2")
    worksheet.update([["init_capital", init_capital]], "B3:C3")
    worksheet.update([["curret_capital", init_capital]], "B4:C4")
    worksheet.update([["collateral_long", 0]], "B5:C5")
    worksheet.update([["collateral_short", 0]], "B6:C6")
    worksheet.update([["tmux_session_name", tmux_session_name]], "B7:C7")
    worksheet.update([["sheet_created(UTC+0)", datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")]], "B8:C8")

    # Transaction history
    header_list = []
    header_list.append("Timestamp(UTC+0)")

    for symbol in traded_assets:
        header_list.extend([
            f"{symbol}_fetched_price",
            f"{symbol}_position",
            f"{symbol}_entry_price",
            f"{symbol}_amount",
            f"{symbol}_quantity",
        ])

    header_list.extend([
        "open_close", "collateral_long", "collateral_short", "capital"
    ])

    start_col = 2
    row_idx = len(worksheet.col_values(start_col)) + 2
    end_col = start_col + len(header_list) - 1
    update_range = (
        f"{num_to_col(start_col)}{row_idx}:"
        f"{num_to_col(end_col)}{row_idx}"
    )

    worksheet.update([header_list], update_range)
