def get_cell_value(worksheet,
                   cell:str):
    res = worksheet.acell(cell).value

    return res

def update_cell_value(worksheet,
                      cell:str,
                      value):
    worksheet.update([[value]], cell)

    return res