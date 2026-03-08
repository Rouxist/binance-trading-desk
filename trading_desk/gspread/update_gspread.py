import datetime
from gspread.exceptions import APIError
import time

def num_to_col(num):
    col = ""
    while num > 0:
        num, rem = divmod(num - 1, 26)
        col = chr(rem + ord('A')) + col
    return col

def retry_gspread(func, logger=None, max_retries=5):
    """
    Retry any gspread API call on transient 503 errors.
    `func` should be a no-argument callable (use lambda to pass arguments).
    """
    for attempt in range(max_retries):
        try:
            return func()
        except APIError as e:
            if e.response.status_code == 503:
                wait_time = 2 ** attempt  # exponential backoff: 1, 2, 4, 8, 16s
                if logger:
                    logger.warning(f"503 error in {func.__name__}. Error cnt: {attempt+1}. Retrying in {wait_time}s...")
                else:
                    print(f"503 error in {func.__name__}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise  # re-raise non-503 errors
    raise Exception(f"{func.__name__} failed after {max_retries} retries")

def add_transaction_log(
    worksheet,
    positions_to_record,
    open_close: str,
    collateral_long: float,
    collateral_short: float,
    capital: float,
    logger=None
):
    """
    Add a transaction log row to the worksheet, with retry logic for gspread API calls.
    """

    # Compose transaction row
    row_element_list = []

    # Add timestamp
    timestamp_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    row_element_list.append(timestamp_now)

    # Add transaction logs
    for position in positions_to_record:
        row_element_list.extend([
            position.fetched_price,
            position.position,
            position.entry_price,
            position.amount,
            position.quantity,
        ])

    # Add account info
    row_element_list.extend([open_close, collateral_long, collateral_short, capital])

    # Determine row index safely
    start_col = 2
    col_values = retry_gspread(lambda: worksheet.col_values(start_col), logger=logger, max_retries=5)
    row_idx = len(col_values) + 1

    # Compute range
    end_col = start_col + len(row_element_list) - 1
    update_range = f"{num_to_col(start_col)}{row_idx}:{num_to_col(end_col)}{row_idx}"

    # Update worksheet safely
    retry_gspread(lambda: worksheet.update([row_element_list], update_range), logger=logger, max_retries=5)
