import math

def get_min_order_quantity(api_handler, 
                           symbol:str):
    """
    Calculate the minimum order quantity for an asset.
    The calculation is mainly based on data retrieved from the '/fapi/v1/exchangeInfo' endpoint.
    (docs: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Exchange-Information)
    In the response, the specifications of each crypto in the 'symbols' attribute are utilized.

    Example: BTCUSDT specifications from `response["symbols"]`:

    ```json
    {
     'symbol': 'BTCUSDT', 
     'pair': 'BTCUSDT', 
     'contractType': 'PERPETUAL', 
     ... 
     'quantityPrecision': 3, 
     ...
     'filters': [
                 ...
                 {
                 'minQty': '0.001', 
                 'stepSize': '0.001', 
                 'maxQty': '120', 
                 'filterType': 'MARKET_LOT_SIZE'
                 }, 
                 {
                 'notional': '100', 
                 'filterType': 'MIN_NOTIONAL'
                 },
                 ...
                 ], 
     'orderTypes': ['LIMIT', 'MARKET', 'STOP', 'STOP_MARKET', 'TAKE_PROFIT', 'TAKE_PROFIT_MARKET', 'TRAILING_STOP_MARKET'], 
     'timeInForce': ['GTC', 'IOC', 'FOK', 'GTX', 'GTD'], 
     'permissionSets': ['GRID', 'COPY', 'DCA', 'PSB']
    }
    ```

    Key variables
    ---
    - In 'MIN_NOTIONAL' filter, 'notional'='100' means that an order for BTCUSDT
      must have a minimum notional value of 100 USDT, before leverage.
    - In 'MARKET_LOT_SIZE' filter, 
        - 'minQty'='0.001' means the minimum order quantity is 0.001.
        - 'stepSize'='0.001' means order quantities must be in increment of 0.001.
    - Additionally, 'markPrice' is retrieved from the '/fapi/v1/premiumIndex' endpoint
      to utilize **real-time** fair price information for the asset.
      - docs: https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Mark-Price

    Main calculation
    ---
    - Let filters = response["filters"]. Following two calculations are primarily considered
      when determining the minimum order quantity for an asset.
        1. min_qty = filters['MARKET_LOT_SIZE']['minQty'] : minimum **quantity** that must be orderd.
        2. min_notional = filters['MIN_NOTIONAL']['notional'] : minimum **amount** that must be orderd.
          - Dividing it by **markPrice** yields another minimun quantity candidate.

    - temp = max{min_qty, min_notioanl}
    - final_min_qty = ceil(temp/stepsize)*stepsize
    
    Example
    ---
    - For BTCUSDT, let min_notional = 100.0, mark_price = 94778.14413043, min_qty = 0.001.
    - Then, min_notional/mark_price = 0.0010550955699489524.
    - Therefore, temp = max{min_notional/mark_price, min_qty} = 0.0010550955699489524.
    - temp = 0.0010550955699489524 must be rounded up using the equation `ceil(temp/step_size)*step_size`.
    - Final minimum order quantity: 0.002.
    """

    exchange_info = api_handler.get_exchange_info() # Fetches min_notional and min_qty

    min_notional = 0
    premium_index = api_handler.get_premium_index(symbol=symbol) # Fetch mark_price for each crypto. real-time.
    mark_price = float(premium_index["markPrice"])

    asset_info = next((asset for asset in exchange_info["symbols"] if asset["symbol"] == symbol), None)

    if not asset_info:
        raise ValueError(f"'{symbol}' does now exist.")

    if asset_info["status"] != "TRADING":
        raise Exception(f"{symbol} is not tradable.")
    
    filters = {f['filterType']: f for f in asset_info['filters']}
    if 'MIN_NOTIONAL' in filters:
        min_notional = float(filters['MIN_NOTIONAL']['notional'])
        
    if 'MARKET_LOT_SIZE' in filters:
        min_qty = float(filters['MARKET_LOT_SIZE']['minQty'])
        step_size = float(filters['MARKET_LOT_SIZE']['stepSize'])
    else:
        raise Exception(f"{symbol} does not support market order.")
    
    temp = max(min_notional/mark_price, min_qty)
    final_min_qty = math.ceil(temp/step_size)*step_size
    
    return final_min_qty
