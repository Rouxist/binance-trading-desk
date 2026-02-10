import datetime
import hashlib
import hmac
from requests import Session, exceptions
from requests.exceptions import Timeout, HTTPError, RequestException
from urllib.parse import urlencode
import time
from typing import Optional

class APIHandler:
    def __init__(self,
                 binance_api_key:str,
                 binance_secret_key:str):
        self.base_url = "https://fapi.binance.com"
        self.session = Session()
        self.binance_api_key = binance_api_key
        self.binance_secret_key = binance_secret_key


    def fetch(self,
              endpoint:str,
              method:str, 
              *,
              headers: Optional[dict]=None,
              params: Optional[dict]=None,
              data: Optional[dict]=None,
              signed: bool=False,
              timeout: int = 10):

        url = self.base_url + endpoint

        params = params.copy() if params else {}
        headers = headers.copy() if headers else {}

        if signed:
            params.setdefault(
                "timestamp",
                int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
            )

            query_string = urlencode(params)
            signature = hmac.new(
                self.binance_secret_key.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            params["signature"] = signature
            headers["X-MBX-APIKEY"] = self.binance_api_key
            
        try:
            response = self.session.request(method=method.upper(),
                                            url=url,
                                            headers=headers,
                                            params=params,
                                            data=data,
                                            timeout=timeout)

            json_response = response.json()
            response.raise_for_status()

        except Timeout as e:
            raise RuntimeError("Request timed out") from e

        except HTTPError as e:
            raise RuntimeError(
                f"HTTP error {response.status_code} for {url}: {response.text}"
            ) from e

        except RequestException as e:
            raise RuntimeError(f"Request failed for {url}") from e

        if json_response is not None:
            return json_response


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
