from .position_model import Position

class PositionCalculator:
    def __init__(self, strategy_name, n_traded_assets):
        self.supported_strategy_list = ["momentum1"]

        if strategy_name not in self.supported_strategy_list:
            raise Exception("Strategy name is not valid")

        self.strategy_name = strategy_name
        self.n_traded_assets = n_traded_assets
    
    def get_positions(self, data):
        if self.strategy_name == "momentum1":
            # check if data shape is valid for this strategy
            # else raise Exception
            # calc positions from data of (13, n_traded_assets)
            positions: List[Position] = []
            return positions
