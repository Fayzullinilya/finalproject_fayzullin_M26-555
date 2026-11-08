# valutatrade_hub\core\models.py
import hashlib
import secrets
from datetime import UTC, datetime

from valutatrade_hub.core.exceptions import InsufficientFundsError


class User:
    def __init__(self, user_id: int, username: str, hashed_password: str,
                 salt: str, registration_date: datetime | None = None
    ):
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id должен быть положительным целым числом")
        self._user_id = user_id

        self.username = username # сеттер

        if not hashed_password or len(hashed_password) != 64:
            raise ValueError("hashed_password должен быть SHA‑256 хешем (64 символа)")
        self._hashed_password = hashed_password

        if not salt or len(salt) != 32:
            raise ValueError("salt должен быть 16 байт (32 hex-символа)")
        self._salt = salt

        self.registration_date = registration_date # сеттер

    # --- Геттеры ---

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    # --- Сеттеры с валидацией ---

    @username.setter
    def username(self, value: str):
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = value.strip()

    @registration_date.setter
    def registration_date(self, value: datetime | None = None):
        if value is None:
            value = datetime.now(UTC)

        if not isinstance(value, datetime):
            raise TypeError("registration_date должен быть объектом datetime")

        now = datetime.now(UTC)
        if value > now:
            raise ValueError(f"Дата регистрации не может быть в будущем (сейчас: {now}, передано: {value})")

        self._registration_date = value

    # --- Методы ---

    def get_user_info(self) -> dict:
        """Возвращает словарь с информацией о пользователе (без пароля и соли)."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "registration_date": self.registration_date.isoformat()
        }

    def change_password(self, new_password: str) -> None:
        """Изменяет пароль пользователя. Генерирует новую соль и новый хеш."""
        if not new_password or len(new_password) < 4:
            raise ValueError("Пароль должен содержать не менее 4 символов.")
        
        new_salt = secrets.token_hex(16)
        self._salt = new_salt

        byte_str = (new_password + new_salt).encode('utf-8')
        self._hashed_password = hashlib.sha256(byte_str).hexdigest()

    def verify_password(self, password: str) -> bool:
        """
        Проверяет пароль: хеширует введенный пароль с сохраненной солью и сравнивает
        с хешем.
        """
        if not password or len(password) < 4:
            return False

        byte_str = (password + self.salt).encode('utf-8')
        hash_str = hashlib.sha256(byte_str).hexdigest()

        return secrets.compare_digest(hash_str, self._hashed_password)

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Создает объект User из словаря (например, из строки JSON)."""
        reg_date_str = data.get("registration_date", None)
        if reg_date_str:
            try:
                reg_date = datetime.fromisoformat(reg_date_str)
            except ValueError as e:
                raise ValueError(
                    f"Некорректный формат registration_date: {reg_date_str!r}"
                ) from e
        else:
            reg_date = None
        obj = cls(data["user_id"], data["username"], data["hashed_password"],
                  data["salt"],reg_date)
        return obj

    def to_dict(self) -> dict:
        """Преобразует объект в словарь для сохранения в JSON."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "hashed_password": self.hashed_password,
            "salt": self.salt,
            "registration_date": self.registration_date.isoformat()
        }

class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        if not currency_code or not isinstance(currency_code, str):
            raise ValueError("currency_code должен быть непустой строкой")
        self.currency_code = currency_code.strip().upper()

        # Используем сеттер для валидации начального баланса
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("balance должен быть числом (int или float)")
        if value < 0:
            raise ValueError("balance не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        if not isinstance(amount, (int, float)):
            raise TypeError("amount должен быть числом")
        if amount <= 0:
            raise ValueError("amount должен быть положительным числом")
        self._balance += float(amount)

    def withdraw(self, amount: float) -> bool:
        """
        Снимает средства, если баланс позволяет.
        Возвращает True при успехе, False если недостаточно средств.
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("amount должен быть числом")
        if amount <= 0:
            raise ValueError("amount должен быть положительным числом")

        amount_f = float(amount)
        if amount_f > self._balance:
            raise InsufficientFundsError(
                available = self.balance,
                required = amount,
                code = self.currency_code
            )

        self._balance -= amount_f
        return True

    def get_balance_info(self) -> dict:
        """Возвращает информацию о балансе."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }

class Portfolio:

    def __init__(self, user_id: int,
                 wallets: dict[str, "Wallet"] | None = None, 
                 rates: dict | None = None):
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id должен быть положительным целым числом")
        self._user_id = user_id

        # Инициализируем пустой словарь или принимаем переданный
        self._wallets = wallets if wallets is not None else {}
        # Сохраняем курсы внутри модели, чтобы get_total_value мог ими пользоваться
        self._rates = rates if rates is not None else {}

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def user(self):
        return self._user_id

    @property
    def wallets(self) -> dict[str, "Wallet"]:
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> None:
        """Добавляет новый кошелёк для указанной валюты, если его ещё нет."""
        if not currency_code or not isinstance(currency_code, str):
            raise ValueError("currency_code должен быть непустой строкой")

        code = currency_code.strip().upper()

        if code in self._wallets:
            raise ValueError(f"Кошелёк для валюты {code} уже существует")

        new_wallet = Wallet(currency_code=code, balance=0.0)
        self._wallets[code] = new_wallet

    def get_wallet(self, currency_code: str) -> "Wallet | None":
        """Возвращает объект Wallet по коду валюты или None, если не найден."""
        if not currency_code or not isinstance(currency_code, str):
            return None
        code = currency_code.strip().upper()
        return self._wallets.get(code)

    def get_total_value(self, base_currency: str = "USD") -> float:
        """
        Возвращает общую стоимость портфеля в указанной базовой валюте.
        Сигнатура строго по заданию: только base_currency.
        Логика расчёта использует self._rates, переданные в конструкторе.
        """
        base_currency = base_currency.upper()
        base_rate = self._rates.get(base_currency, 1.0)
        
        # Защита от деления на ноль, если курс базовой валюты вдруг 0
        if base_rate == 0:
            base_rate = 1.0

        total_value = 0.0
        for code, wallet in self.wallets.items():
            # Курс текущей валюты к базовой: rate_code / rate_base
            code_rate = self._rates.get(code, 0.0)
            value_in_base = wallet.balance * (code_rate / base_rate)
            total_value += value_in_base

        return total_value

    @classmethod
    def from_dict(cls, data: dict, rates: dict | None = None) -> "Portfolio":
        user_id = data.get("user_id")
        raw_wallets = data.get("wallets", {})
        
        wallets = {}
        for code, w_data in raw_wallets.items():
            balance = w_data.get("balance", 0.0)
            wallets[code.upper()] = Wallet(currency_code=code.upper(), balance=balance)
        
        return cls(user_id=user_id, wallets=wallets, rates=rates)

    def to_dict(self) -> dict:
        wallets_data = {}
        for code, wallet in self.wallets.items():
            wallets_data[code] = {
                "currency_code": wallet.currency_code,
                "balance": wallet.balance,
            }
        
        return {
            "user_id": self.user_id,
            "wallets": wallets_data,
        }