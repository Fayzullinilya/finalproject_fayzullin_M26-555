import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

class User:
    def __init__(self, user_id: int, username: str, hashed_password: str,
                 salt: str, registration_date: Optional[datetime] = None
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
    def registration_date(self, value: Optional[datetime] = None):
        if value is None:
            value = datetime.now(timezone.utc)

        if not isinstance(value, datetime):
            raise TypeError("registration_date должен быть объектом datetime")

        now = datetime.now(timezone.utc)
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
                reg_date = datetime.fromisoformat(reg_date_str.replace('Z', '+00:00'))
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
            return False

        self._balance -= amount_f
        return True

    def get_balance_info(self) -> dict:
        """Возвращает информацию о балансе."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }

class Portfolio:
    _exchange_rates = {
        "USD": 1.0,
        "EUR": 1.1,      # 1 EUR = 1.1 USD
        "BTC": 42000.0,  # 1 BTC = 42000 USD
        "GBP": 1.25,     # 1 GBP = 1.25 USD
        "JPY": 0.0065,   # 1 JPY = 0.0065 USD
    }

    def __init__(self, user_id: int, wallets: dict[str, "Wallet"] | None = None):
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id должен быть положительным целым числом")
        self._user_id = user_id

        # Инициализируем пустой словарь или принимаем переданный
        if wallets is None:
            self._wallets: dict[str, "Wallet"] = {}
        else:
            # Проверка: ключи — строки, значения — Wallet
            for code, wallet in wallets.items():
                if not isinstance(code, str):
                    raise TypeError(
                        "Ключи словаря wallets должны быть строками (коды валют)"
                    )
                if not isinstance(wallet, Wallet):
                    raise TypeError(
                        f"Значение для валюты {code} должно быть объектом Wallet"
                    )
            self._wallets = wallets

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
        Считает общую стоимость всех валют в портфеле в указанной базовой валюте.
        Использует фиксированные курсы из _exchange_rates.
        Если курс для какой-то валюты не найден — она не учитывается.
        """
        base_currency = base_currency.strip().upper()
        if base_currency not in self._exchange_rates:
            raise ValueError(f"Курс для базовой валюты {base_currency} не задан")

        base_rate = self._exchange_rates[base_currency]
    
        total = 0.0
        for code, wallet in self._wallets.items():
            if code not in self._exchange_rates:
                raise ValueError(f"Курс для валюты {code} не задан")

            rate_to_usd = self._exchange_rates[code]
            # Конвертируем в USD, затем в base_currency (если base_currency != USD)
            # Формула: balance * rate_to_usd / base_rate
            value_in_base = wallet.balance * rate_to_usd / base_rate
            total += value_in_base

        return total
