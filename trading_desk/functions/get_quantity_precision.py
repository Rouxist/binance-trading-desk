import math

def get_quantity_precision(api_handler, 
                           symbol:str):
    """
    Retrieve the quantity precision for an asset using the '/fapi/v1/exchangeInfo' endpoint.
    """

    exchange_info = api_handler.get_exchange_info() # Fetches min_notional and min_qty

    asset_info = next((asset for asset in exchange_info["symbols"] if asset["symbol"] == symbol), None)

    quantity_precision = asset_info["quantityPrecision"]

    return quantity_precision
