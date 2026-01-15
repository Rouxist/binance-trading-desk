from dataclasses import dataclass

@dataclass
class Position:
    symbol: str
    position: int
    fetched_price: float       # Price fetched right before executing the order through the API
    entry_price: float         # Price finalized when the order is executed
    quantity: float
    amount: float
