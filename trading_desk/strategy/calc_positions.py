from .position_model import Position

class PositionCalculator:
    def __init__(self, strategy_name, n_traded_assets):
        self.strategy_name = strategy_name
        self.n_traded_assets = n_traded_assets
    
    def get_positions(self, data):
        if self.strategy_name == "momentum1":
            # calc positions from data of (13, n_traded_assets)
            positions: List[Position] = []
            return positions
        else:
            raise Exception("Strategy name is not valid")
