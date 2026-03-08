from gspread.exceptions import APIError
import time

def get_cell_value(worksheet, cell: str, logger=None, max_retries=5):
    """
    Safely fetch a single cell value, retrying on transient 503 errors.
    """
    for attempt in range(max_retries):
        try:
            return worksheet.acell(cell).value
        except APIError as e:
            if e.response.status_code == 503:
                wait_time = 2 ** attempt  # exponential backoff: 1, 2, 4, 8, 16 s
                if logger:
                    logger.warning(f"503 error in {func.__name__}. Error cnt: {attempt+1}. Retrying in {wait_time}s...")
                else:
                    print(f"503 error on {cell}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise  # re-raise non-503 errors
    raise Exception(f"Failed to fetch cell {cell} after {max_retries} retries")

def update_cell_value(worksheet,
                      cell:str,
                      value):
    worksheet.update([[value]], cell)

    return res
