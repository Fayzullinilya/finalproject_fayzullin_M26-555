import os
from dataclasses import dataclass

@dataclass(frozen=True)
class ParserConfig:
    #  API ключ из переменной окружения
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY")

    # Эндпоинты
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_URL: str = "https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"

    # Списки отслеживаемых валют
    FIAT_CURRENCIES: tuple[str, ...] = ("EUR", "RUB", "GBP", "JPY", "CNY")
    CRYPTO_CURRENCIES: tuple[str, ...] = ("BTC", "ETH", "SOL")

    # Маппинг тикеров для CoinGecko
    CRYPTO_ID_MAP: dict[str, str] = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana"
    }

    # Параметры
    BASE_FIAT_CURRENCY: str = "USD"
    REQUEST_TIMEOUT: int = 10
    RATE_TTL_SEC: int = 300
    UPDATE_INTERVAL_SEC: int = 60

    # Пути к файлам
    RATES_CACHE_PATH: str = os.path.join("data","rates.json")
    EXCHANGE_RATES_PATH: str  = os.path.join("data","exchange_rates.json")

# Создание синглтона на уровне модуля
PARSER_CONFIG = ParserConfig()
