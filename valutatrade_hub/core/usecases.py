# valutatrade_hub/core/usecases.py

def register_user(username: str, password: str) -> int:
    # Заглушка: просто возвращаем ID, чтобы код не падал
    # В тестах мы всё равно заменим эту функцию на MagicMock
    return 1

def login_user(username: str, password: str) -> int:
    return 1

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
