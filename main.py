# Import packages
import os
import json
from apscheduler.schedulers.blocking import BlockingScheduler

# Import functions, classes
from data_models.config_models import MainConfig, StrategyConfig
from trading_desk import TradingDesk

# Import environment variables
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')


# Main code
if __name__ == "__main__":
    # Configuration setup
    with open("config.json") as f:
        raw = json.load(f)
    raw["strategyconfig"] = StrategyConfig(**raw["strategyconfig"])
    config = MainConfig(**raw)

    # Print out configurations
    print("================================ ENV var ================================")
    print("api key:", BINANCE_API_KEY)
    print("secret key:", BINANCE_SECRET_KEY)
    print()
    print("================================ Configs ================================")
    print("description:", config.description)
    print("is_mock:", config.is_mock)
    print("traded_assets:", config.traded_assets)
    print()
    print("=========================== Strategy Configs ============================")
    print("strategy_name:", config.strategyconfig.strategy_name)
    print("unit:", config.strategyconfig.unit)
    print("every:", config.strategyconfig.every)
    print("n_asset_buy:", config.strategyconfig.n_asset_buy)
    print("n_asset_sell:", config.strategyconfig.n_asset_sell)
    print("asset_weight_type:", config.strategyconfig.asset_weight_type)
    print()
    print()

    # Run strategy
    print("================================== Run ==================================")

    # runner = StrategyRunner(strategy_func=strategy_momentum)
    # scheduler = BlockingScheduler()

    # if config.strategyconfig.unit == "m":
    #     scheduler.add_job(runner.run_job, "cron", minute=f"*/{config.strategyconfig.every}")
    # elif config.strategyconfig.unit == "h":
    #     scheduler.add_job(runner.run_job, "cron", hour=f"*/{config.strategyconfig.every}", minute=0)

    trading_desk = TradingDesk(is_mock=config.is_mock, 
                               strategy_name=config.strategyconfig.strategy_name,
                               n_traded_assets=config.traded_assets)
    scheduler = BlockingScheduler()

    if config.strategyconfig.unit == "m":
        scheduler.add_job(trading_desk.run_strategy, "cron", minute=f"*/{config.strategyconfig.every}")
    elif config.strategyconfig.unit == "h":
        scheduler.add_job(trading_desk.run_strategy, "cron", hour=f"*/{config.strategyconfig.every}", minute=0)

    scheduler.start()
