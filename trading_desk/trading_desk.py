import time
import math
from .data_models import MainConfig
from .setup_logger import setup_logger, log_configs
from .gspread import init_gspread, setup_worksheet_format, add_transaction_log
from .strategy import PositionCalculator
from .strategy.position_model import Position
from .functions import APIHandler, build_closing_price_series, build_dataframe, get_quantity_precision, get_min_order_quantity

__all__ = ["TradingDesk"]


class TradingDesk:
    def __init__(self, config:MainConfig, binance_api_key:str, binance_secret_key:str):
        # Hyperparameters
        self.is_mock = config.is_mock

        self.binance_api_key = binance_api_key
        self.binance_secret_key = binance_secret_key

        self.session_name = config.session_name
        self.tmux_session_name = config.tmux_session_name
        self.strategy_name = config.strategyconfig.strategy_name

        if config.n_traded_assets != len(config.traded_assets):
            raise ValueError(
                f"traded_assets contains {len(config.traded_assets)} elements, but n_traded_assets is set to {config.n_traded_assets}."
            )
        
        self.traded_assets = config.traded_assets
        self.n_traded_assets = config.n_traded_assets
        
        self.init_capital = config.init_capital
        
        self.unit = config.strategyconfig.unit
        self.every = config.strategyconfig.every
        self.n_asset_buy = config.strategyconfig.n_asset_buy
        self.n_asset_sell = config.strategyconfig.n_asset_sell
        self.asset_weight_type = config.strategyconfig.asset_weight_type

        # Exchange hyperparameters
        self.transaction_cost = 0.0005

        # Attributes
        self.capital = config.init_capital
        self.running_capital = 0
        self.collateral_long = 0
        self.collateral_short = 0
        self.positions_holding: List[Position] = []

        # Objects
        self.api_handler = APIHandler(binance_api_key=self.binance_api_key,
                                      binance_secret_key=self.binance_secret_key)
        self.position_calculator = PositionCalculator(strategy_name=self.strategy_name)

        # Initialization
        ## Logger
        self.logger = setup_logger(session_name=self.session_name, 
                                   strategy_name=self.strategy_name, 
                                   log_console=True)
        
        ## Configuration logging
        self.logger.info("TradingDesk is instantiated.")
        self.logger.info(f"Binance API key    = {self.binance_api_key}")
        self.logger.info(f"Binance SECRET key = {self.binance_secret_key}")
        log_configs(logger=self.logger, config=config)

        ## Gspread initialization
        self.g_worksheets_mock = init_gspread(session_name=self.session_name)

        setup_worksheet_format(worksheet=self.g_worksheets_mock,
                               strategy_name=self.strategy_name, 
                               init_capital=self.init_capital,
                               traded_assets=self.traded_assets,
                               tmux_session_name=self.tmux_session_name)


    def strategy_func(self):
        self.logger.info("strategy_func is executed")

        """
        Step 1
        : Close existing positions
        """
        self.logger.info("Step 1 starts.")

        if self.positions_holding: # If positions_holding is not empty
            cleared_positions = [] # Also includes assets that were not held

            for position in self.positions_holding[:]: # Iterate over a shallow copy
                if position.quantity > 0 : # If currently holding this asset
                    if self.is_mock:
                        fetched_price = self.api_handler.get_current_price(symbol=position.symbol)
                        
                        position_for_clearing = -1*position.position
                        quantity_holding = position.quantity
                        amount_to_be_cleared = -1*position_for_clearing*fetched_price * quantity_holding

                        amount_clearing_after_fee = amount_to_be_cleared*(1 + position_for_clearing*self.transaction_cost)

                        cleared_position = Position(
                                            symbol=position.symbol,
                                            position=position_for_clearing,
                                            fetched_price=fetched_price,
                                            entry_price=fetched_price,
                                            quantity=position.quantity,
                                            amount=amount_clearing_after_fee
                                        )

                        # Update balance status
                        if position.position==1:
                            self.collateral_long -= abs(position.amount)
                        if position.position==-1:
                            self.collateral_short -= abs(position.amount)

                        self.capital += amount_clearing_after_fee
                        
                    else:
                        pass
                        # if positions.position == 1:
                        #     res = place_market_sell(symbol=position.symbol)
                        # elif positions.position == -1:
                        #     res = place_market_buy(symbol=position.symbol)
                        # if res == success:
                        #     self.positions_holding.append(position)
                        # else:
                        #     self.logger.info(f"{position.position} order of {position.symbol} was not successfully cleared")           

                else:
                    cleared_position = Position(
                                           symbol=position.symbol,
                                           position=0,
                                           fetched_price=0,
                                           entry_price=0,
                                           quantity=0,
                                           amount=0
                                       )
                
                cleared_positions.append(cleared_position)
                self.positions_holding.remove(position)
     
            # After 

            add_transaction_log(worksheet=self.g_worksheets_mock,
                                positions_to_record=cleared_positions,
                                open_close="close",
                                collateral_long=self.collateral_long,
                                collateral_short=self.collateral_short,
                                capital=self.capital)
        
            if not self.positions_holding: # If self.positions_holding is empty
                self.logger.info("All positions are cleared")

            self.logger.info(f"After step 1, cleared_positions = {cleared_positions}")

        else:
            self.logger.info("No open position. Position clearing has been skipped.")

        self.logger.info("Step 1 is finished.")


        """
        Step 2
        : Position calculation
        """
        time.sleep(10) # delay to prevent fetching incomplete kline
        self.logger.info("Step 2 starts.")

        # Fetch data and build DataFrame
        close_prices = {}

        for symbol in self.traded_assets:
            klines = self.api_handler.fetch_klines(symbol=symbol,
                                                   every=self.every,
                                                   unit=self.unit,
                                                   timesteps=13)
            close_prices[symbol] = build_closing_price_series(klines)

        df = build_dataframe(close_prices)
        df = df.iloc[:-1] # Exclude very last row which is incomplete kline
        
        positions = self.position_calculator.get_positions(data=df,
                                                           n_asset_buy=self.n_asset_buy,
                                                           n_asset_sell=self.n_asset_sell)

        symbols_to_trade = [p.symbol for p in positions]
        self.logger.info(f"Symbols to trade: {[f"{p.symbol}:{p.position}" for p in positions]}")

        self.logger.info("Step 2 is finished.")


        """
        Step 3
        : Open new positions
        """
        self.logger.info("Step 3 starts.")

        # Calculate budget allocation (amount) for each asset
        if self.asset_weight_type=="equal":
            amount = self.capital / (self.n_asset_buy+self.n_asset_sell)

            for position in positions:
                position.amount = amount

        else:
            raise NotImplementedError(f"Asset weight type '{self.asset_weight_type}' is not supported yet")

        # Make (mock) order for each asset
        for symbol in self.traded_assets:
            position = next((p for p in positions if p.symbol == symbol), None)

            if symbol in symbols_to_trade:
                fetched_price = self.api_handler.get_current_price(symbol=position.symbol)
                position.fetched_price = fetched_price

                quantity_precision = get_quantity_precision(api_handler=self.api_handler,
                                                            symbol=symbol)
                
                factor = 10**quantity_precision
                quantity = position.amount/fetched_price # Order quantity is calculated using last-traded-price fetched from '/fapi/v1/ticker/price'.
                quantity_rounded_down = math.floor(quantity*factor)/factor # round down at quantity precision decimal points

                min_order_quantity = get_min_order_quantity(api_handler=self.api_handler,
                                                            symbol=symbol)

                ## Do NOT place order if calculated quantity is less then minimum order quantity
                if quantity_rounded_down < min_order_quantity:
                    self.logger.info(f"Order for {symbol} is not executed because "
                                     f"the calculated order quantity {quantity_rounded_down} is "
                                     f"below the current minimum order quantity {min_order_quantity}.")
                    
                    position.quantity = -1
                    position.entry_price = 0
                    position.amount = 0
                    self.positions_holding.append(position)
                    continue

                ## Order placement
                if self.is_mock:
                    """
                    Fee deduction example: open short -> close with long
                    
                    Quantity |  Price  | Position | Executed |     Fee    | Fee deducted |  balance
                    ---------------------------------------------------------------------------------
                             |         |          |          |            |              |  6.742414
                         3.1 |  2.1915 |       -1 |  6.7937  | 0.00339683 |       6.7903 | 13.532667
                         3.1 |  2.1908 |        1 | -6.7915  | 0.00339574 |      -6.7949 |  6.737791
                    """
                    order_amount = -1*position.position*quantity_rounded_down*fetched_price              # `Executed`
                    order_amount_after_fee = order_amount*(1 + position.position*self.transaction_cost)  # `Fee deducted`
                    
                    position.quantity = quantity_rounded_down
                    position.entry_price = fetched_price
                    position.amount = order_amount_after_fee

                    # Update balance status
                    if position.position==1:
                        self.collateral_long += abs(order_amount_after_fee)
                    if position.position==-1:
                        self.collateral_short += abs(order_amount_after_fee)

                    self.capital += order_amount_after_fee

                else:
                    # Determine side
                    if position.position == 1:
                        side = "BUY"
                    elif position.position == -1:
                        side = "SELL"

                    # Place order
                    res = self.api_handler.place_market_order(symbol=position.symbol,
                                                              side=side, 
                                                              quantity=quantity_rounded_down)
                    
                    if res["status"] != "FILLED":
                        err = RuntimeError(
                            f"Order not filled: status={res["status"]}"
                        )

                        raise err
                    
                    # Update position information based on the response
                    position.quantity = float(res["executedQty"]) # negative if short position
                    position.entry_price = float(res["avgPrice"])
                    order_amount_after_fee = float(res["cumQuote"])*(1 + position.position*self.transaction_cost)  # `Fee deducted`
                    position.amount = order_amount_after_fee

                    # Update balance status
                    if position.position==1:
                        self.collateral_long += abs(order_amount_after_fee)
                    if position.position==-1:
                        self.collateral_short += abs(order_amount_after_fee)

                    self.capital += order_amount_after_fee

            else:
                position = Position(
                               symbol=symbol,
                               position=0,
                               fetched_price=0,
                               entry_price=0,
                               quantity=0,
                               amount=0
                           )


            self.positions_holding.append(position)

        add_transaction_log(worksheet=self.g_worksheets_mock,
                            positions_to_record=self.positions_holding,
                            open_close="open",
                            collateral_long=self.collateral_long, 
                            collateral_short=self.collateral_short,
                            capital=self.capital)
        
        self.logger.info(f"After step 3, positions_holding = {self.positions_holding}")
        
        self.logger.info("Step 3 is finished.")


    def run_strategy(self,
                     scheduler):

        try:
            self.strategy_func()

        except Exception as e:
            self.logger.exception("Error occurred")

            if hasattr(e, "wrong_dataframe"):
                self.logger.error("Wrong dataframe:\n%s",
                                  e.wrong_dataframe.to_string())

            scheduler.shutdown(wait=False)
