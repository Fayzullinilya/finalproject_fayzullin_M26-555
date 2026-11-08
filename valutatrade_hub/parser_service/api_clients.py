from abc import ABC, abstractmethod
from datetime import UTC, datetime

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import PARSER_CONFIG


class BaseApiClient(ABC):
    
    @abstractmethod
    def fetch_rates(self) -> dict:
        """Возвращает курсы в формате {"BTC_USD": 59337.21, ...}."""


class CoinGeckoClient(BaseApiClient):
    """Получает курсы криптовалют к базовой через CoinGecko."""

    def __init__(self):
        self._url = PARSER_CONFIG.COINGECKO_URL

    def fetch_rates(self) -> dict:
        base = PARSER_CONFIG.BASE_FIAT_CURRENCY.lower()
        ids = ",".join(
            PARSER_CONFIG.CRYPTO_ID_MAP[code]
            for code in PARSER_CONFIG.CRYPTO_CURRENCIES
        )
        params = {
            "ids": ids,
            "vs_currencies": base
        }

        try:
            response = requests.get(self._url, params=params,
                                    timeout=PARSER_CONFIG.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка запроса к CoinGecko: {e}") from e

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = {}
        for code in PARSER_CONFIG.CRYPTO_CURRENCIES:
            gecko_id = PARSER_CONFIG.CRYPTO_ID_MAP[code]
            try:
                result[code] = {
                    "rate": data[gecko_id][base],
                    "timestamp": now,
                    "source": "coingecko"
                }
            except (KeyError, TypeError):
                raise ApiRequestError(f"CoinGecko не вернул курс для {code}")
        return result


class ExchangeRateApiClient(BaseApiClient):
    """Получает курсы фиатных валют к базовой через exchangerate-api."""

    def __init__(self):
        self._url = PARSER_CONFIG.EXCHANGERATE_URL

    def fetch_rates(self) -> dict:
        # Проверяем переменную окружения в методе, что бы процесс 
        # не падал при создании объекта
        if PARSER_CONFIG.EXCHANGERATE_API_KEY is None:
            raise ValueError(
                "API ключ отсутсвует. Не установлено значение переменной "
                "окружения EXCHANGERATE_API_KEY"
            )

        url = self._url.format(
            api_key=PARSER_CONFIG.EXCHANGERATE_API_KEY,
            base_currency=PARSER_CONFIG.BASE_FIAT_CURRENCY
        )

        try:
            response = requests.get(url, timeout=PARSER_CONFIG.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка запроса к ExchangeRate API: {e}") from e

        # Проверяем статус
        if data.get("result") != "success":
            raise ApiRequestError(
                f"ExchangeRate API вернул ошибку: {data.get('error-type')}"
            )

        # Получаем словарь курсов
        rates = data.get("conversion_rates")
        if not isinstance(rates, dict):
            raise ApiRequestError("ExchangeRate API вернул неожиданный формат ответа")

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = {}
        for fiat in PARSER_CONFIG.FIAT_CURRENCIES:
            rate = rates.get(fiat)
            if not isinstance(rate, (int, float)) or rate <= 0:
                raise ApiRequestError(f"ExchangeRate API не вернул корректный курс для {fiat}")
            result[fiat] = {
                "rate": 1.0 / rate,
                "timestamp": now,
                "source": "ExchangeRate-API"
            }
        return result