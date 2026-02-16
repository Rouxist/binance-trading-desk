def get_cell_value(worksheet,
                   cell:str):
    res = worksheet.acell(cell).value

    return res