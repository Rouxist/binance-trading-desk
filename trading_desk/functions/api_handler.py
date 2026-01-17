import datetime
from requests import Session, exceptions
from requests.exceptions import Timeout, HTTPError, RequestException
import time
from typing import Optional

class APIHandler:
    def __init__(self):
        self.base_url = "https://fapi.binance.com"
        self.session = Session()


    def fetch(self,
              endpoint:str,
              method:str, 
              *,
              headers: Optional[dict]=None,
              params: Optional[dict]=None,
              data: Optional[dict]=None,
              timeout: int = 10):

        url = self.base_url + endpoint
        
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
