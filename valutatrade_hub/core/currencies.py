# currencies.py
from abc import ABC, abstractmethod

class CurrencyNotFoundError(Exception):
    """Исключение, если код валюты не найден в реестре."""
    pass


class Currency(ABC):
    def __init__(self, name: str, code: str):
        clean_code = code.strip().upper()
        if not (2 <= len(clean_code) <= 5):
            raise ValueError(f"code должна быть длиной от 2 до 5 символов: {clean_code}")
        if any(c.isspace() for c in clean_code):
            raise ValueError("code не должна содержать пробелов")
        if not name or not name.strip():
            raise ValueError("name должна быть непустой строкой")

        self.name = name.strip()
        self.code = clean_code

    @abstractmethod
    def get_display_info(self) -> str:
        pass

    def __repr__(self):
        return f"<Currency {self.code}: {self.name}>"


class FiatCurrency(Currency):
    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country.strip()

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        if market_cap < 0:
            raise ValueError("market_cap не может быть отрицательным")
        self.algorithm = algorithm.strip()
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        mcap_str = f"{self.market_cap:.2e}" if self.market_cap >= 1e9 else f"{self.market_cap:,.2f}"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap_str})"


# Реестр валют: словарь внутри модуля — это нормально для фабрики
_CURRENCY_DICT: dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "JPY": FiatCurrency("Japanese Yen", "JPY", "Japan"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 5.4e11),
}


def get_currency(code: str) -> Currency | None:
    """
    Фабрика: возвращает объект валюты по коду или None, если код неизвестен.
    Нормализует код (верхний регистр) перед поиском.
    """
    normalized_code = code.strip().upper()
    if normalized_code not in _CURRENCY_DICT:
        raise CurrencyNotFoundError(f"Валюта с кодом '{normalized_code}' не найдена в реестре")
  
    return _CURRENCY_DICT.get(normalized_code)
