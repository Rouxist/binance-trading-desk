import pandas as pd
from .position_model import Position
from .strat_momentum1 import strat_momentum1

class PositionCalculator:
    def __init__(self, strategy_name):
        self.supported_strategy_list = ["momentum1"]

        if strategy_name not in self.supported_strategy_list:
            raise Exception("Strategy name is not valid")

        self.strategy_name = strategy_name


    def get_positions(self, 
                      data,
                      n_asset_buy,
                      n_asset_sell):
        if not isinstance(data, pd.DataFrame):
            raise TypeError(
                f"Expected pd.DataFrame, got {type(data).__name__}"
            )
        
        if self.strategy_name == "momentum1":
            if len(data) != 13:
                raise ValueError(
                    f"DataFrame must have exactly 13 rows, got {len(data)}"
                )
            
            symbols_top, symbols_bottom = strat_momentum1(data=data,
                                                          n_asset_buy=n_asset_buy,
                                                          n_asset_sell=n_asset_sell)

            positions: List[Position] = []

            for symbol_top in symbols_top:
                pos = Position(
                                symbol=symbol_top,
                                position=1,
                                fetched_price=None,
                                entry_price=None,
                                quantity=None,
                                amount=None
                            )
                positions.append(pos)
            
            for symbol_bottom in symbols_bottom:
                pos = Position(
                                symbol=symbol_bottom,
                                position=-1,
                                fetched_price=None,
                                entry_price=None,
                                quantity=None,
                                amount=None
                            )
                positions.append(pos)

            return positions
