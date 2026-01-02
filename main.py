# Import packages
import os
import json
from apscheduler.schedulers.blocking import BlockingScheduler

# Import functions, classes
from trading_desk.data_models import MainConfig, StrategyConfig
from trading_desk import TradingDesk

# Import environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")


# Main code
if __name__ == "__main__":
    # Configuration setup
    with open("config.json") as f:
        raw = json.load(f)
    raw["strategyconfig"] = StrategyConfig(**raw["strategyconfig"])
    config = MainConfig(**raw)

    # TradingDesk instantiation
    trading_desk = TradingDesk(config=config, 
                               binance_api_key=BINANCE_API_KEY,
                               binance_secret_key=BINANCE_SECRET_KEY)
    
    # Scheduler setup
    scheduler = BlockingScheduler()

    if config.strategyconfig.unit == "m":
        scheduler.add_job(trading_desk.run_strategy, "cron", minute=f"*/{config.strategyconfig.every}")
    elif config.strategyconfig.unit == "h":
        scheduler.add_job(trading_desk.run_strategy, "cron", hour=f"*/{config.strategyconfig.every}", minute=0)

    scheduler.start()
