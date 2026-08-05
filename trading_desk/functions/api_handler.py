import datetime
import hashlib
import hmac
from requests import Session, exceptions
from requests.exceptions import Timeout, HTTPError, RequestException
from urllib.parse import urlencode
import time
import uuid
from typing import Optional

class OrderExecutionUnknown(RuntimeError):
    pass

class APIHandler:
    def __init__(self,
                 binance_api_key:str,
                 binance_secret_key:str):
        self.base_url = "https://fapi.binance.com"
        self.session = Session()
        self.binance_api_key = binance_api_key
        self.binance_secret_key = binance_secret_key

    # Further prevents recvWindow error that again occurred from '/fapi/v2/balance'
    def fetch(self,
              endpoint: str,
              method: str,
              *,
              headers: Optional[dict] = None,
              params: Optional[dict] = None,
              data: Optional[dict] = None,
              signed: bool = False,
              timeout: int = 10,
              max_retries: int = 2):

        url = self.base_url + endpoint

        base_params = params.copy() if params else {}
        headers = headers.copy() if headers else {}

        # Used when handling 10-seconds-timeout
        is_order = endpoint == "/fapi/v1/order" and method.upper() == "POST"
        if signed and is_order: # generate idempotency key for order
            base_params.setdefault("newClientOrderId", str(uuid.uuid4()))

        for attempt in range(max_retries + 1):
            request_params = base_params.copy()

            if signed:
                request_params.pop("signature", None)

                # To prevent recvWindow error that once occurred from '/fapi/v3/positionRisk': 
                # {"code":-1021,"msg":"Timestamp for this request is outside of the recvWindow."}
                server_time = self.get_server_time(is_unix=True)
                local_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
                offset = server_time - local_time

                request_params["timestamp"] = (
                    int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
                    + offset
                )

                request_params.setdefault("recvWindow", 10000)

                query_string = urlencode(request_params)
                signature = hmac.new(
                    self.binance_secret_key.encode("utf-8"),
                    query_string.encode("utf-8"),
                    hashlib.sha256
                ).hexdigest()

                request_params["signature"] = signature
                headers["X-MBX-APIKEY"] = self.binance_api_key

            try:
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=request_params,
                    data=data,
                    timeout=timeout
                )

                try:
                    json_response = response.json()
                except ValueError:
                    json_response = None

                if (
                    signed
                    and response.status_code == 400
                    and isinstance(json_response, dict)
                    and json_response.get("code") == -1021
                    and attempt < max_retries
                ):
                    continue

                response.raise_for_status()
                return json_response

            # To handle occasional Binance read timeout, avoiding duplicate order placement
            # HTTPSConnectionPool(host='fapi.binance.com', port=443): Read timed out. (read timeout=10)
            except Timeout:
                """
                if not (signed and is_order):
                    if attempt < max_retries:
                        time.sleep(1 + attempt)
                        continue
                    raise

                # SAFE HANDLING WHEN TIMEOUT OCCURRED FROM ORDER
                # check if order already exists
                try:
                    check = self.fetch(
                        "/fapi/v1/order",
                        "GET",
                        params={
                            "symbol": request_params["symbol"],
                            "origClientOrderId": request_params["newClientOrderId"]
                        },
                        signed=True
                    )
                    return check  # order already exists

                except Exception:
                    # order not found -> retry
                    if attempt < max_retries:
                        time.sleep(1 + attempt)
                        continue
                    raise
                """
                # To prevent overlapping retry logic with that of place_market_order() (2026.08.04)
                if signed and is_order:
                    # The order may already have executed.
                    # Never continue the outer POST loop.
                    raise OrderExecutionUnknown(
                        "Order request timed out; execution status is unknown."
                    ) from e

                if attempt < max_retries:
                    # for debugging
                    self.logger.info(f"Timeout occurred from fetch(). Retry in {1+attempt} seconds.")
                    time.sleep(1 + attempt)
                    continue
                raise


            except HTTPError as e:
                raise RuntimeError(
                    f"HTTP error {response.status_code} for {url}: {response.text}"
                ) from e

            except RequestException as e:
                raise RuntimeError(f"Request failed for {url}") from e


    # Market data endpoints
    def get_server_time(self,
                        is_unix:bool=True):

        response = self.fetch(endpoint="/fapi/v1/time",
                              method="GET")
        if is_unix:
            return response["serverTime"]
        else:
            return datetime.datetime.utcfromtimestamp(response["serverTime"]/1000)


    def get_exchange_info(self):

        response = self.fetch(endpoint="/fapi/v1/exchangeInfo",
                              method="GET")
        
        return response


    def get_premium_index(self,
                          symbol:str):

        params = {
            "symbol": symbol
        }

        response = self.fetch(endpoint="/fapi/v1/premiumIndex",
                              method="GET",
                              params=params)
        
        return response


    def get_current_price(self, 
                          symbol:str):
        
        params = {
            "symbol": symbol
        }

        response = self.fetch(endpoint="/fapi/v1/ticker/price",
                              method="GET",
                              params=params)
        
        return float(response["price"])


    def fetch_klines(self, 
                     symbol:str,
                     every:int,
                     unit:str,
                     timesteps:int):

        now = datetime.datetime.now(datetime.timezone.utc)

        """
        `'startTime`, `endTime` argument determination example
        - interval="1m"
        - Fetch 13 latest closing prices
        
        If the "/fapi/v1/klines" is called at 10:46:10, then
        - start_time = 2026-02-10 10:33:00+00:00
        - end_time   = 2026-02-10 10:46:00+00:00

        Then fetched result includes total 14 rows (after arranged into pandas.DataFrame):
                                   BTCUSDT  ETHUSDT  XRPUSDT  LTCUSDT  TONUSDT
        open_time                                                             
        2026-02-10 10:33:00+00:00  69025.0  2014.30   1.4197    53.33   1.3469
        2026-02-10 10:34:00+00:00  69020.1  2013.85   1.4186    53.31   1.3467
        2026-02-10 10:35:00+00:00  68988.8  2013.47   1.4172    53.27   1.3478
        2026-02-10 10:36:00+00:00  69009.7  2014.24   1.4174    53.27   1.3480
        2026-02-10 10:37:00+00:00  68986.6  2013.42   1.4166    53.24   1.3478
        2026-02-10 10:38:00+00:00  68951.5  2012.04   1.4159    53.24   1.3471
        2026-02-10 10:39:00+00:00  68944.3  2012.26   1.4164    53.24   1.3477
        2026-02-10 10:40:00+00:00  68970.2  2013.60   1.4174    53.27   1.3478
        2026-02-10 10:41:00+00:00  68969.9  2013.69   1.4172    53.24   1.3480
        2026-02-10 10:42:00+00:00  68974.2  2013.97   1.4166    53.24   1.3474
        2026-02-10 10:43:00+00:00  68987.1  2014.53   1.4169    53.25   1.3479
        2026-02-10 10:44:00+00:00  68964.3  2013.71   1.4165    53.21   1.3468
        2026-02-10 10:45:00+00:00  69012.8  2015.26   1.4170    53.24   1.3474
        2026-02-10 10:46:00+00:00  69005.3  2014.94   1.4163    53.24   1.3473

        Each timestamp represents the open time of the kline.
        For example, if the timestamp is '10:44:00+00:00', 
        the open price corresponds approximately to the price at 10:44:00, 
        and close price corresponds approximately to the price at 10:44:59.

        Therfore, the last row (with timestamp 2026-02-10 10:46:00+00:00) represents
        an incomplete whose closing price has not yet been determined.
        The last row is removed before position calculation.
        """
        if unit=="h":
            # Calc end_time, start_time
            floored = now.replace(minute=0, second=0, microsecond=0)
            aligned_hour = (floored.hour // every) * every # Find last {every}h boundary (e.g. 4h boundaries: 0, 4, 8, 12, 16, 20)
            
            end_time = floored.replace(hour=aligned_hour)
            start_time = end_time - datetime.timedelta(hours=every*timesteps)

            # Convert to milliseconds
            end_time = int(end_time.timestamp() * 1000)
            start_time = int(start_time.timestamp() * 1000)

        elif unit=="m":
            # Calc end_time, start_time
            floored = now.replace(second=0, microsecond=0)
            aligned_minute = (floored.minute // every) * every
            
            end_time = floored.replace(minute=aligned_minute)
            start_time = end_time - datetime.timedelta(minutes=every*timesteps)

            # Convert to milliseconds
            end_time = int(end_time.timestamp() * 1000)
            start_time = int(start_time.timestamp() * 1000)

        else:
            raise NotImplementedError(f"The unit {unit} is not supported yet.")
        


        params = {
            'symbol': symbol,
            'interval': f"{every}{unit}",
            'startTime': start_time,
            'endTime': end_time,
            'limit': 500
        }

        response = self.fetch(endpoint="/fapi/v1/klines",
                              method="GET",
                              params=params)
        
        return response


    # Account-related endpoints
    def get_balance(self,
                    symbol:str):
    
        response = self.fetch(endpoint="/fapi/v2/balance",
                              method="GET",
                              signed=True)

        res = next((bal for bal in response if bal["asset"] == symbol), None)
        
        return res


    def set_leverage(self,
                     symbol:str,
                     leverage:int=1):
        
        params = {
            'symbol': symbol,
            'leverage': leverage
        }

        response = self.fetch(endpoint="/fapi/v1/leverage",
                              method="POST",
                              params=params,
                              signed=True)
        
        """
        Example return foramt:

        {'symbol': 'BTCUSDT', 'leverage': 1, 'maxNotionalValue': '1800000000'}
        """
        return response


    def fetch_position(self,
                       symbol:str):
        """
        Fetch information about currently open positions.
        """
        
        params = {
            'symbol': symbol
        }

        response = self.fetch(endpoint="/fapi/v3/positionRisk",
                              method="GET",
                              params=params,
                              signed=True)
        
        return response
    

    # Order-related endpoints
    def old_place_market_order(self,
                           symbol:str,
                           side:str,
                           quantity:float):
        """
        Place Buy/Sell market order.
        """

        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity,
            "newOrderRespType": "RESULT"
        }

        response = self.fetch(endpoint="/fapi/v1/order",
                              method="POST",
                              params=params,
                              signed=True)
        
        return response


    def place_market_order(self,
                           symbol: str,
                           side: str,
                           quantity: float,
                           reduce_only: bool = False):
        """
        Place Buy/Sell market order safely (handles -1007 timeout).

        - Do not retry POST requests to prevent duplicate order placement
        - Added 'reduceOnly' for position-closing request
        """

        client_order_id = str(uuid.uuid4())

        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity,
            "newOrderRespType": "RESULT",
            "newClientOrderId": client_order_id
        }

        if reduce_only:
            params["reduceOnly"] = "true"

        try:
            response = self.fetch(
                endpoint="/fapi/v1/order",
                method="POST",
                params=params,
                signed=True,
                max_retries=0
            )
            return response

        except Exception as e:
            is_unknown_execution = (
                isinstance(e, OrderExecutionUnknown)
                or "-1007" in str(e) # -1007: Binance Timeout error
            )

            if not is_unknown_execution:
                raise

        # From this point onward, never resend the POST.
        last_error = None

        for delay in (0.5, 1.0, 2.0, 3.0, 5.0):
            time.sleep(delay)
            try:
                return self.fetch(
                    endpoint="/fapi/v1/order",
                    method="GET",
                    params={
                        "symbol": symbol,
                        "origClientOrderId": client_order_id,
                    },
                    signed=True,
                    max_retries=0,
                )

            except Exception as query_error:
                last_error = query_error

                # Ideally inspect a structured Binance error code here.
                if "-2013" in str(query_error):
                    continue

                if isinstance(query_error, OrderExecutionUnknown):
                    continue
                raise

        raise OrderExecutionUnknown(
            "The order request had unknown execution status and could not "
            "be confirmed. The order was not resent. "
            f"symbol={symbol}, clientOrderId={client_order_id}"
        ) from last_error


    def fetch_order(self,
                    symbol: str,
                    order_id: int,
                    max_retries: int = 5,
                    delay: float = 0.3):
        """
        Motivation
        - Response from POST '/fapi/v1/order' may not include 'avgPrice' field
        - This function is to get 'avgPrice' from placed order
        
        Retry Logic
        - Retry when "Order does not exist" error occur. (-2013 error)
          - Can happen when 'GET /fapi/v1/order' is executed immediately after 'POST /fapi/v1/order', because the POST request may take longer to be processed
        """

        params = {
            "symbol": symbol,
            "orderId": order_id,
        }

        last_error = None

        for attempt in range(max_retries):
            try:
                return self.fetch(
                    endpoint="/fapi/v1/order",
                    method="GET",
                    params=params,
                    signed=True,
                )

            except RuntimeError as error:
                last_error = error
                error_message = str(error)

                if '"code":-2013' not in error_message: # Retry only temporary "Order does not exist" responses.
                    raise

                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))

        raise RuntimeError(
            f"Order could not be found after {max_retries} attempts: "
            f"symbol={symbol}, order_id={order_id}"
        ) from last_error
