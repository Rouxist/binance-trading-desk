from dataclasses import dataclass

@dataclass
class Position:
    symbol: str
    position: int
    fetched_price: float
    entry_price: float
    quantity: float
    amount: float
