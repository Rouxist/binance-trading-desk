import datetime
import logging
from logging.handlers import RotatingFileHandler

from .strategy import PositionCalculator

from .strategy.position_model import Position

__all__ = ["TradingDesk"]


class TradingDesk:
    def __init__(self, is_mock, strategy_name, n_traded_assets, g_worksheet=None):
        # Hyperparameters
        if is_mock and g_worksheet is None:
            raise ValueError("'g_worksheet' is required when 'is_mock' is True")
        self.is_mock = is_mock
        self.g_worksheets_mock = g_worksheet
        self.strategy_name = strategy_name
        self.n_traded_assets = n_traded_assets

        # Attributes
        self.positions_holding: List[Position] = []

        # Objects
        self.position_calculator = PositionCalculator(strategy_name = self.strategy_name,
                                                      n_traded_assets = self.n_traded_assets)

        # Initialization
        ## Logger
        self.logger = logging.getLogger("my_app")
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s :: [%(levelname)s] :: %(message)s"
        )

        ### File handler setup
        file_handler = RotatingFileHandler(
            f"./logs/{strategy_name}__{datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.log",
            maxBytes=1024*1024*10,  # 10 MB
            backupCount=5           # up to 5 log files
        )
        file_handler.setFormatter(formatter)

        ### Console handler setup
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        ## Account
        if self.is_mock:
            # Create new google spreadsheet page and initialize
            pass
        else:
            # Clear positions in binance account
            pass
        
        self.logger.info("TradingDesk is created.")

    def strategy_func(self):
        self.logger.info("strategy_func is executed")

        """
        Step 1
        : Close existing positions
        """
        
        if self.positions_holding: # If positions_holding is not empty
            for position in self.positions_holding:
                if self.is_mock:
                    pass
                    # if position.position == 1:
                    #     res = place_mock_market_sell(symbol=position.symbol)
                    # elif positions.position == -1:
                    #     res = place_mock_market_buy(symbol=position.symbol)
                    # if res == success:
                    #     self.positions_holding.remove(position)
                    # else:
                    #     self.logger.info(f"mock {position.position} order of {position.symbol} was not successfully cleared")
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

        """
        Step 2
        : Position calculation
        """

        # data = fetch_data()
        positions = self.position_calculator.get_positions(data=None)


        """
        Step 3
        : Open new positions
        """

        for position in positions:
            if self.is_mock:
                pass
                # if position.position == 1:
                #     res = place_mock_market_buy(symbol=position.symbol)
                # elif positions.position == -1:
                #     res = place_mock_market_sell(symbol=position.symbol)
                # if res == success:
                #     self.positions_holding.append(position)
                # else:
                #     self.logger.info(f"mock {position.position} order of {position.symbol} was not successfully executed")
            else:
                pass
                # if positions.position == 1:
                #     res = place_market_buy(symbol=position.symbol)
                # elif positions.position == -1:
                #     res = place_market_sell(symbol=position.symbol)
                # if res == success:
                #     self.positions_holding.append(position)
                # else:
                #     self.logger.info(f"{position.position} order of {position.symbol} was not successfully executed")

    def run_strategy(self):
        self.strategy_func()
