import datetime

def num_to_col(num):
    col = ""
    while num > 0:
        num, rem = divmod(num - 1, 26)
        col = chr(rem + ord('A')) + col
    return col

def add_transaction_log(worksheet,
                        positions_holding,
                        open_close:str,
                        collateral_long:float, 
                        collateral_short:float,
                        capital:float): # List elements are not type-casted

    # Compose transaction row
    row_element_list = []

    ## Add timestamp
    timestamp_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
    row_element_list.append(timestamp_now)

    ## Add transaction logs
    for position in positions_holding:
        row_element_list.extend([
            position.fetched_price,
            position.position,
            position.entry_price,
            position.amount,
            position.quantity,
        ])

    ## Add account info
    row_element_list.extend([open_close, collateral_long, collateral_short, capital])

    # Update worksheet
    start_col = 2
    row_idx = len(worksheet.col_values(start_col)) + 1
    end_col = start_col + len(row_element_list) - 1
    update_range = (
        f"{num_to_col(start_col)}{row_idx}:"
        f"{num_to_col(end_col)}{row_idx}"
    )

    worksheet.update([row_element_list], update_range)
