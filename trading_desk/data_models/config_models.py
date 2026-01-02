from dataclasses import dataclass
from typing import List, Dict

# Configuration data models
@dataclass
class StrategyConfig:
    strategy_name: str
    unit: str
    every: int
    n_asset_buy: int
    n_asset_sell: int
    asset_weight_type: str

@dataclass
class MainConfig:
    session_name: str
    tmux_session_name: str
    description: str
    is_mock: bool
    traded_assets: List[str]
    n_traded_assets: int
    strategyconfig: StrategyConfig
