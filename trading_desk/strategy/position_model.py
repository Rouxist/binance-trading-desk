from dataclasses import dataclass

@dataclass
class Position:
    symbol: str
    position: int
    entry_price: float
    quantity: float
    amount: float
