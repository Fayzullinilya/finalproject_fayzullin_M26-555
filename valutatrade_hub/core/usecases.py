# valutatrade_hub\core\usecases.py
import hashlib
import secrets
from datetime import datetime, timezone
from valutatrade_hub.core.utils import JsonStorage


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
            if user.get("username") == username:
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
            if u.get("username") == username:
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

def show_portfolio(user_id: int, base_currency: str) -> dict:
    return {
        "user": "test",
        "total": 0.0,
        "currencies": {}
    }

def buy_currency(currency: str, amount: float) -> dict:
    return {"rate": 1.0, "cost": amount, "prev_qty": 0.0, "new_qty": amount}

def sell_currency(currency: str, amount: float) -> dict:
    return {"rate": 1.0, "revenue": amount, "prev_qty": amount, "new_qty": 0.0}

def get_rate(from_cur: str, to_cur: str) -> dict:
    return {"forward": 1.0, "reverse": 1.0, "updated_at": "now"}
