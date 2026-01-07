from .data_models import MainConfig
from .setup_logger import setup_logger, log_configs
from .gspread import init_gspread, setup_worksheet_format
from .strategy import PositionCalculator
from .strategy.position_model import Position

__all__ = ["TradingDesk"]


class TradingDesk:
    def __init__(self, config:MainConfig, binance_api_key:str, binance_secret_key:str):
        # Hyperparameters
        self.is_mock = config.is_mock

        self.binance_api_key =binance_api_key
        self.binance_secret_key = binance_secret_key

        self.session_name = config.session_name
        self.tmux_session_name = config.tmux_session_name
        self.strategy_name = config.strategyconfig.strategy_name
        self.traded_assets = config.traded_assets
        self.n_traded_assets = config.n_traded_assets
        self.init_capital = config.init_capital
        
        self.unit = config.strategyconfig.unit
        self.every = config.strategyconfig.every
        self.n_asset_buy = config.strategyconfig.n_asset_buy
        self.n_asset_sell = config.strategyconfig.n_asset_sell
        self.asset_weight_type = config.strategyconfig.asset_weight_type

        # Attributes
        self.positions_holding: List[Position] = []

        # Objects
        self.position_calculator = PositionCalculator(strategy_name = self.strategy_name,
                                                      n_traded_assets = self.n_traded_assets)

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

        ## Account initialization
        if self.is_mock:
            self.g_worksheets_mock = init_gspread(session_name=self.session_name)

            setup_worksheet_format(worksheet=self.g_worksheets_mock,
                                   strategy_name=self.strategy_name, 
                                   init_capital=self.init_capital,
                                   traded_assets=self.traded_assets,
                                   tmux_session_name=self.tmux_session_name)
        else:
            # Clear positions in binance account
            pass


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
