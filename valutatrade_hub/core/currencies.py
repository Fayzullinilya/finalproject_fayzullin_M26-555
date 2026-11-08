# currencies.py
from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError
from valutatrade_hub.infra.settings import SettingsLoader


class Currency(ABC):

    def __init__(self, name: str, code: str):
        name = name.strip()
        code = code.replace(" ", "").strip().upper()
        if not name:
            raise ValueError("Наименование валюты не должно быть пустой строкой.")        
        if not (2 <= len(code) <= 5):
            raise ValueError("Код валюты должен быть длиной от 2 до 5 символов.")
        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        pass

    @classmethod
    def get_currency(cls, code: str) -> "Currency":
        code = code.replace(" ", "").strip().upper()
        settings = SettingsLoader()
        currency_reg = settings.get("CURRENCY_REGISTRY", {})
        data = currency_reg.get(code, "")
        if data is None:
            available = ", ".join(currency_reg.keys())
            raise CurrencyNotFoundError(code, available)
        if data["type"] == "fiat":
            return FiatCurrency(data["name"], code, data["country"])
        return CryptoCurrency(data["name"], code, data["algorithm"], data["market_cap"])

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
        return(
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )