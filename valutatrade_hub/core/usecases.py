# valutatrade_hub\core\usecases.py
import hashlib
import secrets
from datetime import datetime, timezone
from valutatrade_hub.core.utils import JsonStorage
from valutatrade_hub.core.models import Portfolio, Wallet
from valutatrade_hub.core.currencies import Currency

class Auth:
    def __init__(self):
        # todo: сделать отдельный файл
        self.users_storage = JsonStorage("data/users.json")
        self.portfolios_storage = JsonStorage("data/portfolios.json")

    def register_user(self, username, password):
        # Валидация входных данных
        if not username or not isinstance(username, str):
            raise ValueError("Имя пользователя не может быть пустым.")

        if not password or len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")

        # Загрузка пользователей
        users = self.users_storage.read()

        # Проверка уникальности username
        for user in users:
            if user.get("username", '').lower() == username.lower():
                raise ValueError(f"Имя пользователя '{username}' уже занято")

        # Генерация user_id (автоинкремент)
        user_id = 1
        if users:
            last_id = max((user.get("user_id", 0) for user in users), default=0)
            user_id = last_id + 1 if last_id > 0 else 1

        # Генерация соли и хеша
        salt = secrets.token_hex(16)
        hashed_password = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

        # Генерируем дату в UTC, сразу в нужном формате: с +00:00 вместо Z
        reg_date = datetime.now(timezone.utc)
        registration_date_str = reg_date.isoformat()  
        # например: 2025-11-03T14:22:10.123456+00:00

        # Формирование записи пользователя
        new_user = {
            "user_id": user_id,
            "username": username,
            "hashed_password": hashed_password,
            "salt": salt,
            "registration_date": registration_date_str
        }

        # Сохранение пользователя
        users.append(new_user)
        self.users_storage.write(users)

        # Создание пустого портфеля для пользователя
        portfolios = self.portfolios_storage.read()
        new_portfolio = {
            "user_id": user_id,
            "wallets": {}
        }
        portfolios.append(new_portfolio)
        self.portfolios_storage.write(portfolios)

        return user_id

    def login_user(self, username, password):
        if not username:
            raise ValueError("Имя пользователя не может быть пустым.")
        if not password:
            raise ValueError("Пароль не может быть пустым.")

        users = self.users_storage.read()

        # Поиск пользователя по username
        user = None
        for u in users:
            if u.get("username", '').lower() == username.lower():
                user = u
                break

        if user is None:
            raise ValueError(f"Пользователь '{username}' не найден")

        # Проверка пароля
        # Здесь нужнно использовать User.verify_password
        salt = user.get("salt", "")
        expected_hash = user.get("hashed_password", "")
        provided_hash = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

        if provided_hash != expected_hash:
            raise ValueError("Неверный пароль")

        # Успешный вход: возвращаем user_id
        return user["user_id"]

class PortfolioService:
        
    def __init__(self):
        self.portfolios_storage = JsonStorage("data/portfolios.json")
        # Cделать загрузку курсов из API
        self.rates_storage = JsonStorage("data/rates.json", dict)        

    def _load_portfolio(self, user_id):
        """Загружает портфель пользователя и маппит JSON в объекты Wallet."""
        portfolios_data = self.portfolios_storage.read()

        portfolio_data = None
        for p in portfolios_data:
            if p.get("user_id") == user_id:
                portfolio_data = p
                break

        if portfolio_data is None:
            return None

        rates = self._load_rates()

        wallets_raw = portfolio_data.get("wallets", {})
        wallets = {}

        # wallets_raw: {"BTC": {"currency_code": "BTC", "balance": 0.05}, ...}
        for code, data in wallets_raw.items():
            # data: {"currency_code": "...", "balance": ...}
            balance = data.get("balance", 0.0)
            wallets[code] = Wallet(code, balance)

        return Portfolio(user_id, wallets, rates)

    def _save_portfolio(self, portfolio):
        portfolios_data = self.portfolios_storage.read()

        new_wallets = {}
        for code, wallet in portfolio.wallets.items():
            new_wallets[code] = {
                "currency_code": code,
                "balance": wallet.balance,
            }

        found = False
        for p in portfolios_data:
            if p.get("user_id") == portfolio.user_id:
                p["wallets"] = new_wallets
                found = True
                break

        if not found:
            portfolios_data.append({
                "user_id": portfolio.user_id,
                "wallets": new_wallets,
            })

        self.portfolios_storage.write(portfolios_data)

    def _load_rates(self):
        """Читает rates.json и возвращает плоский словарь {code: rate_to_USD}."""
        data = self.rates_storage.read()
            
        rates_flat = {}
            
        for pair_key, info in data.items():
            if not isinstance(info, dict) or "rate" not in info:
                continue
                
            parts = pair_key.split("_")
            if len(parts) != 2:
                continue
                
            from_code, to_code = parts[0], parts[1]
                
            if to_code == "USD":
                rates_flat[from_code] = float(info["rate"])
            
        if "USD" not in rates_flat:
            rates_flat["USD"] = 1.0
                
        return rates_flat
    
    def show_portfolio(self, user_id, base_currency="USD"):
        portfolio = self._load_portfolio(user_id)
        if portfolio is None:
            rates = self._load_rates()
            portfolio = Portfolio(user_id, {}, rates)

        base_curr_obj = Currency.get_currency(base_currency)
        total_value = portfolio.get_total_value(base_curr_obj.code)

        currencies = {}
        for code, wallet in portfolio.wallets.items():
            try:
                rate_to_usd = portfolio._rates[code]
                base_rate = portfolio._rates.get(base_curr_obj.code, 1.0)
                value_in_base = wallet.balance * rate_to_usd / base_rate
                currencies[code] = {
                    "qty": wallet.balance,
                    "value": value_in_base,
                }
            except KeyError:
                currencies[code] = {
                    "qty": wallet.balance,
                    "value": 0.0,
                }

        return {
            "user": str(user_id),
            "total": total_value,
            "currencies": currencies,
        }

    def buy_currency(self, user_id, currency, amount):
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise ValueError("Количество покупаемой валюты должен быть числом.")
        if amount <= 0:
            raise ValueError("Сумма покупки должна быть положительным числом.")

        currency_obj = Currency.get_currency(currency)

        portfolio = self._load_portfolio(user_id)
        if portfolio is None:
            portfolio = Portfolio(user_id, {})

        wallet = portfolio.get_wallet(currency_obj.code)
        prev_qty = wallet.balance if wallet else 0.0

        if wallet is None:
            portfolio.add_currency(currency_obj.code)
            wallet = portfolio.get_wallet(currency_obj.code)

        wallet.deposit(amount)
        new_qty = wallet.balance

        self._save_portfolio(portfolio)

        rate = portfolio._rates.get(currency_obj.code, 0.0)
        cost = amount * rate

        return {
            "rate": rate,
            "cost": cost,
            "prev_qty": prev_qty,
            "new_qty": new_qty,
        }

    def sell_currency(self, user_id, currency, amount):
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            raise ValueError("Количество покупаемой валюты должен быть числом.")
        if amount <= 0:
            raise ValueError("Сумма покупки должна быть положительным числом.")

        currency_obj = Currency.get_currency(currency)

        portfolio = self._load_portfolio(user_id)
        if portfolio is None:
            portfolio = Portfolio(user_id, {})

        wallet = portfolio.get_wallet(currency_obj.code)
        prev_qty = wallet.balance if wallet else 0.0

        if wallet is None:
            raise ValueError(
                f"У вас нет кошелька {currency_obj.code}. Добавьте валюту: она создаётся "
                "автоматически при первой покупке."
            )
        
        wallet.withdraw(currency_obj.code)

        new_qty = wallet.balance
        rate = portfolio._rates.get(currency_obj.code, 0.0)
        revenue = amount * rate

        self._save_portfolio(portfolio)

        return {
            "rate": rate,
            "revenue": revenue,
            "prev_qty": prev_qty,
            "new_qty": new_qty,
        }

    def get_rate(self, from_currency: str, to_currency: str):
        """
        Возвращает курс конвертации FROM -> TO.
        
        Логика:
          - Все курсы в системе хранятся как курс к USD.
          - Курс FROM->TO = rate[TO] / rate[FROM]
        
        Возвращает dict:
          {
            "from": "EUR",
            "to": "BTC",
            "rate": 0.00023,          # прямой курс FROM -> TO
            "inverse_rate": 4347.8,  # обратный курс TO -> FROM
            "base": "USD",           # базовая валюта, относительно которой хранятся курсы
            "missing": [],           # список валют, которых нет в курсах (пусто, если всё ок)
            "is_valid": True/False   # можно ли доверять курсу
          }
        """

        from_curr_obj = Currency.get_currency(from_currency)
        to_curr_obj = Currency.get_currency(to_currency)

        rates = self._load_rates()

        rate_from = rates.get(from_curr_obj.code, 0.0)
        rate_to = rates.get(to_curr_obj.code, 0.0)

        # Конвертация через USD: rate = rate_to / rate_from
        rate = rate_to / rate_from if rate_from != 0 else None
        inverse_rate = 1.0 / rate if rate and rate != 0 else None

        return {
            "from": from_curr_obj.code,
            "to": to_curr_obj.code,
            "rate": rate,
            "inverse_rate": inverse_rate,
            "base": "USD",
            "missing": [],
            "is_valid": True,
        }