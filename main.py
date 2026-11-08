#!/usr/bin/env python3

import argparse
import logging
import threading

from valutatrade_hub.cli.interface import CLI
from valutatrade_hub.logging_config import setup_logging
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import PARSER_CONFIG
from valutatrade_hub.parser_service.scheduler import UpdateScheduler
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


def start_scheduler():
    """Собирает зависимости парсера и запускает цикл обновления."""
    storage = RatesStorage(
        data_dir=PARSER_CONFIG.DATA_PATH,
        journal_file=PARSER_CONFIG.EXCHANGE_RATES_FILE,
        snapshot_file=PARSER_CONFIG.RATES_CACHE_FILE
    )
    updater = RatesUpdater(
        clients=[CoinGeckoClient(), ExchangeRateApiClient()],
        storage=storage
    )
    UpdateScheduler(updater).run()

def main():

    # Определяем уровень логирования (параметр --gebug в командной строке)
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(level=log_level)     

    # Запускаем фоновый процесс обновления курсов
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()

    # Запускаем CLI интерфейс
    cli = CLI()
    cli.run()

if __name__ == "__main__":
    main()