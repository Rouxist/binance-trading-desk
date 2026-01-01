import datetime

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
        if self.is_mock:
            # Create new google spreadsheet page and initialize
            pass
        else:
            # Clear positions in binance account
            pass

        print("TradingDesk is created.")

    def strategy_func(self):
        print("strategy_func is executed at:", datetime.datetime.now())

        """
        Step 1
        : Close existing positions
        """
        
        if self.positions_holding: # If positions_holding is not empty
            for ticker in self.positions_holding:
                if self.is_mock:
                    pass
                    # if position is buy:
                    #     place_mock_market_sell()
                    # else:
                    #     place_mock_market_buy()
                else:
                    pass
                    # if position is buy:
                    #     place_market_sell()
                    # else:
                    #     place_market_buy()


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
                #     logger.warning()
            else:
                pass
                # if positions.position == 1:
                #     res = place_market_buy(symbol=position.symbol)
                # elif positions.position == -1:
                #     res = place_market_sell(symbol=position.symbol)
                # if res == success:
                #     self.positions_holding.append(position)
                # else:
                #     logger.warning()

    def run_strategy(self):
        self.strategy_func()
