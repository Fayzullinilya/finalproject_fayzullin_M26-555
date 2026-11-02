# tests/test_interface.py
import pytest

def test_run_exits_on_exit_command(cli, mock_prompt):
    mock_prompt.string.side_effect = ["", "exit"]
    cli.run()
    assert mock_prompt.string.call_count == 2

def test_process_command_unknown_command(cli, capsys):
    cli.process_command("unknown-command-xyz")
    out, _ = capsys.readouterr()
    assert "Неизвестная команда: 'unknown-command-xyz'" in out

def test_process_command_shlex_error(cli, capsys):
    # Незакрытая кавычка — shlex выбросит ValueError
    cli.process_command('echo "unclosed quote')
    out, _ = capsys.readouterr()
    assert "Ошибка ввода: проверьте кавычки" in out

# --- Парсер _get_arg_value ---

def test_get_arg_value_single_value(cli):
    args = ["cmd", "--base", "EUR"]
    val = cli._get_arg_value(args, "--base")
    assert val == "EUR"

def test_get_arg_value_missing_value_raises(cli):
    args = ["cmd", "--base"]
    with pytest.raises(ValueError, match="Не указано значение"):
        cli._get_arg_value(args, "--base")

def test_get_arg_value_multiple_values_raises(cli):
    args = ["cmd", "--base", "USD", "--base", "EUR"]
    with pytest.raises(ValueError, match="несколько значений"):
        cli._get_arg_value(args, "--base")

# --- Регистрация ---

def test_handle_register_calls_usecase(cli, mock_usecases):
    cli.handle_register(["register", "--username", "alice", "--password", "secret"])
    mock_usecases["register_user"].assert_called_once_with("alice", "secret")

def test_handle_register_missing_args(cli, capsys):
    cli.handle_register(["register"])
    out, _ = capsys.readouterr()
    assert "аргументы --username и --password обязательны" in out

# --- Логин ---

def test_handle_login_sets_current_user_id(cli, mock_usecases):
    mock_usecases["login_user"].return_value = 999
    cli.handle_login(["login", "--username", "bob", "--password", "pass123"])
    assert cli.current_user_id == 999

def test_handle_login_missing_args(cli, capsys):
    cli.handle_login(["login"])
    out, _ = capsys.readouterr()
    assert "аргументы --username и --password обязательны" in out

# --- show-portfolio: проверка авторизации ---

def test_handle_show_portfolio_requires_login(cli, capsys, mock_usecases):
    cli._set_current_user(None)
    cli.handle_show_portfolio(["show-portfolio"])
    out, _ = capsys.readouterr()
    assert "Вы не вошли в систему" in out
    mock_usecases["show_portfolio"].assert_not_called()

# --- show-portfolio: флаг --base не передан (должен быть USD) ---

def test_handle_show_portfolio_default_currency(cli, capsys, mock_usecases):
    mock_usecases["login_user"].return_value = 1
    cli.handle_login(["login", "--username", "test", "--password", "123"])

    mock_usecases["show_portfolio"].return_value = {
        "user": "test",
        "total": 500.0,
        "currencies": {"USD": {"qty": 500.0, "value": 500.0}}
    }

    cli.handle_show_portfolio(["show-portfolio"])  # без --base

    out, _ = capsys.readouterr()
    assert "Портфель пользователя 'test' (база: USD):" in out
    assert "- USD: 500.0000 → 500.00 USD" in out
    assert "ИТОГО: 500.00 USD" in out

# --- show-portfolio: передан корректный --base ---

def test_handle_show_portfolio_with_base_currency(cli, capsys, mock_usecases):
    mock_usecases["login_user"].return_value = 2
    cli.handle_login(["login", "--username", "alice", "--password", "secret"])

    mock_usecases["show_portfolio"].return_value = {
        "user": "alice",
        "total": 1234.56,
        "currencies": {
            "EUR": {"qty": 1.2345, "value": 110.0},
            "BTC": {"qty": 0.5, "value": 1124.56}
        }
    }

    cli.handle_show_portfolio(["show-portfolio", "--base", "EUR"])

    out, _ = capsys.readouterr()
    assert "Портфель пользователя 'alice' (база: EUR):" in out
    assert "- EUR: 1.2345 → 110.00 EUR" in out
    assert "- BTC: 0.5000 → 1124.56 EUR" in out
    assert "ИТОГО: 1,234.56 EUR" in out

# --- show-portfolio: неверный код валюты ---

def test_handle_show_portfolio_invalid_currency_format(cli, capsys, mock_usecases):
    # <--- ВАЖНО: Явно задаем ID пользователя, иначе _current_user_id будет None или Mock
    mock_usecases["login_user"].return_value = 999 
    
    cli.handle_login(["login", "--username", "bad", "--password", "pwd"])
    
    # Теперь проверяем, что пользователь вошел (это нормально для этого теста)
    # Но главное - мы проверяем реакцию на --base
    cli.handle_show_portfolio(["show-portfolio", "--base", "ABCD123"])

    out, _ = capsys.readouterr()
    
    assert "не является кодом валюты в формате стандарта ISO" in out
    # show_portfolio НЕ должен вызываться, так как мы не дошли до него из-за ошибки валидации
    mock_usecases["show_portfolio"].assert_not_called()


# --- show-portfolio: пустой портфель (нет кошельков) ---

def test_handle_show_portfolio_empty_currencies(cli, capsys, mock_usecases):
    mock_usecases["login_user"].return_value = 4
    cli.handle_login(["login", "--username", "empty", "--password", "x"])

    mock_usecases["show_portfolio"].return_value = {
        "user": "empty",
        "total": 0.0,
        "currencies": {}
    }

    cli.handle_show_portfolio(["show-portfolio"])

    out, _ = capsys.readouterr()
    assert "Портфель пользователя 'empty' (база: USD):" in out
    assert "Кошельков нет." in out
    assert "ИТОГО: 0.00 USD" in out

# --- buy: проверка авторизации и аргументов ---

def test_handle_buy_requires_login(cli, capsys, mock_usecases):
    cli._set_current_user(None)
    cli.handle_buy(["buy", "--currency", "BTC", "--amount", "1.5"])
    out, _ = capsys.readouterr()
    assert "Вы не вошли в систему" in out
    mock_usecases["buy_currency"].assert_not_called()

def test_handle_buy_success(cli, capsys, mock_usecases):
    # --- НАСТРОЙКА МОКА (самое важное) ---
    # 1. Логин должен вернуть int, иначе CLI не поймёт, что пользователь вошёл
    mock_usecases["login_user"].return_value = 5
    
    # 2. buy_currency должен вернуть ЧИСТОЙ словарь с float/int. 
    # Никаких MagicMock внутри значений!
    mock_usecases["buy_currency"].return_value = {
        "rate": 50000.0,
        "cost": 75000.0,
        "prev_qty": 0.0,
        "new_qty": 1.5
    }
    # ----------------------------------

    # Выполняем логин
    cli.handle_login(["login", "--username", "buyer", "--password", "pwd"])
    
    # Выполняем покупку
    cli.handle_buy(["buy", "--currency", "BTC", "--amount", "1.5"])

    out, _ = capsys.readouterr()
    
    assert "Покупка выполнена: 1.5000 BTC" in out
    assert "по курсу 50000.00 BTC/USD" in out
    assert "- BTC: было 0.0000 → стало 1.5000" in out
    assert "Оценочная стоимость покупки: 75,000.00 USD" in out


def test_handle_sell_success(cli, capsys, mock_usecases):
    # --- НАСТРОЙКА МОКА ---
    mock_usecases["login_user"].return_value = 6
    
    mock_usecases["sell_currency"].return_value = {
        "rate": 48000.0,
        "revenue": 72000.0,
        "prev_qty": 2.0,
        "new_qty": 0.5
    }
    # ---------------------

    cli.handle_login(["login", "--username", "seller", "--password", "pwd"])
    cli.handle_sell(["sell", "--currency", "BTC", "--amount", "1.5"])

    out, _ = capsys.readouterr()
    
    assert "Продажа выполнена: 1.5000 BTC" in out
    assert "по курсу 48000.00 BTC/USD" in out
    assert "- BTC: было 2.0000 → стало 0.5000" in out
    assert "Оценочная выручка: 72,000.00 USD" in out


# --- get-rate: базовый успех ---

def test_handle_get_rate_success(cli, capsys, mock_usecases):
    mock_usecases["get_rate"].return_value = {
        "forward": 1.12345678,
        "reverse": 0.890123,
        "updated_at": "2026-11-02T10:00:00Z"
    }

    cli.handle_get_rate(["get-rate", "--from", "EUR", "--to", "USD"])

    out, _ = capsys.readouterr()
    assert "Курс EUR→USD: 1.12345678 (обновлено: 2026-11-02T10:00:00Z)" in out
    assert "Обратный курс USD→EUR: 0.89" in out  # .2f округлит до 0.89
