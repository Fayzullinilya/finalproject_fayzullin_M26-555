import prompt
import shlex

from typing import Callable, List, Dict, Optional, Any

from core.usecases import (
    register_user,
    login_user,
    show_portfolio,
    buy_currency,
    sell_currency,
    get_rate,
)

# Глобальная сессия: None — не залогинен, иначе — имя пользователя


class CLI:
    def __init__(self):
        self._current_user_id = None
        self.commands = {
            "register": self.handle_register,
            "login": self.handle_login,
            "show-portfolio": self.handle_show_portfolio,
            "buy": self.handle_buy,
            "sell": self.handle_sell,
            "get-rate": self.handle_get_rate,
            "help": self.handle_help,
        }

    @property
    def current_user_id(self) -> int | None:
        return self._current_user_id

    def _set_current_user(self, user_id: int | None) -> None:
        # внутренний мтод. текущий пользоватеь может меняться тольо через команду login
        self._current_user_id = user_id

    def _is_logged_in(self) -> bool:
        return self._current_user_id is not None

    def _get_arg_value(self, args: list[str], key: str) -> str | None:
        found_values = []
        i = 0
        while i < len(args):
            if args[i] == key:
                if len(args) <= i + 1 or args[i+1].startswith("-"):
                    raise ValueError(f"Не указано значение для '{key}'")
                found_values.append(args[i+1])
                i += 2
                continue
            i += 1
        if not found_values:
            return None
        if len(found_values) > 1:
            raise ValueError(
                f" Для '{key}' указано несколько значений: {', '.join(found_values)}. "
            )
        return found_values[0]
    
    # ------------------------------------------------------------------
    # Основной цикл
    # ------------------------------------------------------------------

    def run(self) -> None:
        while True:
            try:
                user_input = prompt.string('\n>>>Введите команду: ')
            except (EOFError, KeyboardInterrupt):
                print("\nВыход из CLI.")
                break

            if user_input.strip().lower() == "exit":
                break

            self.process_command(user_input)

    def process_command(self, command_line: str) -> None:
        try:
            args = shlex.split(command_line, posix=False)
        except ValueError as e:
            print(f"Ошибка ввода: проверьте кавычки ({e})")
            return

        if not args:
            return

        command = args[0].lower()

        if command not in self.commands:
            print(f"Неизвестная команда: '{command}'. Введите 'help' для справки.")
            return

        handler = self.commands[command]
        handler(args)

    # ------------------------------------------------------------------
    # Хендлеры
    # ------------------------------------------------------------------

    def handle_help(self, args: list[str]) -> None:
        print("Доступные команды:")
        print(" - register --username <name> --password <pass>")
        print(" - login --username <name> --password <pass>")
        print(" - show-portfolio [--base <USD>]")
        print(" - buy --currency <code> --amount <qty>")
        print(" - sell --currency <code> --amount <qty>")
        print(" - get-rate --from <code> --to <code>")

    def handle_register(self, args: list[str]) -> None:

        try:
            username = self._get_arg_value(args, '--username')
            password = self._get_arg_value(args, '--password')
        except ValueError as e:
            print(str(e))

        if username is None or password is None:
            print("Ошибка: аргументы --username и --password обязательны.")
            return

        username = username.strip()
        # пробелы в начале и конце пароля недопустимы
        password = password.strip()

        if not username or not password:
            print("Ошибка: имя и пароль не могут быть пустыми.")
            return

        try:
            user_id = register_user(username, password)
            print(
                f"Пользователь '{username}' зарегистрирован (id={user_id}). "
                f"Войдите: login --username {username} --password ****"
            )
        except ValueError as e:
            print(str(e))
        except FileNotFoundError:
            print("Не удалось сохранить данные: файл базы не найден.")
        except Exception as e:
            print(f"Не удалось зарегистрировать пользователя: {e}")

    def handle_login(self, args: list[str]) -> None:
        try:
            username = self._get_arg_value(args, '--username')
            password = self._get_arg_value(args, '--password')
        except ValueError as e:
            print(str(e))

        if username is None or password is None:
            print("Ошибка: аргументы --username и --password обязательны.")
            return

        username = username.strip()
        # пробелы в начале и конце пароля недопустимы
        password = password.strip()

        if not username or not password:
            print("Ошибка: имя и пароль не могут быть пустыми.")
            return

        try:
            user_id = login_user(username, password)
            self._set_current_user_id(user_id)
            print(f"Вы вошли как '{username}'.")
        except ValueError as e:
            print(str(e))
        except Exception as e:
            print(f"Не удалось войти: {e}")

    def handle_show_portfolio(self, args: list[str]) -> None:
        if not self._is_logged_in():
            print(
                "Вы не вошли в систему. "
                "Выполните: login --username <имя пользователя> --password <пароль>"
            )            
            return

        base_currency = "USD"

        try:
            currency = self._get_arg_value(args, '--base')
        except ValueError as e:
            print(str(e))

        if (len(currency) == 3 and currency.isalpha() and currency.isascii()):
            base_currency = currency.upper()
        else:
            print(
                f"Ошибка: {currency} не является кодом валюты в  "
                "формате стандарта ISO (например: EUR, RUB)."
            )
            return
            
        try:
            data = show_portfolio(self._current_user_id, base_currency)
            user = data["user"]
            total = data["total"]
            currencies = data.get("currencies", {})

            print(f"Портфель пользователя '{user}' (база: {base_currency}):")
            if not currencies:
                print("  Кошельков нет.")
                print(f"ИТОГО: 0.00 {base_currency}")
                return

            for cur, info in currencies.items():
                qty = info["qty"]
                value = info["value"]
                print(f"- {cur}: {qty:.4f} → {value:.2f} {base_currency}")

            print("-" * 32)
            print(f"ИТОГО: {total:,.2f} {base_currency}")
        except KeyError as e:
            print(f"Ошибка данных портфеля: отсутствует поле {e}")
        except ValueError as e:
            print(str(e))
        except Exception as e:
            print(f"Не удалось показать портфель: {e}")

    def handle_buy(self, args: list[str]) -> None:
        if not self._is_logged_in():
            print(
                "Вы не вошли в систему. "
                "Выполните: login --username <имя пользователя> --password <пароль>"
            )            
            return

        try:
            currency = self._get_arg_value(args, '--currency')
            amount = self._get_arg_value(args, '--amount')
        except ValueError as e:
            print(str(e))

        if currency is None or amount is None:
            print("Ошибка: аргументы --currency и --amount обязательны.")
            return

        try:
            result = buy_currency(currency, amount)
            rate = result["rate"]
            cost = result["cost"]
            prev_qty = result.get("prev_qty", 0)
            new_qty = result["new_qty"]

            print(
                f"Покупка выполнена: {amount:.4f} {currency} "
                f"по курсу {rate:.2f} {currency}/USD"
            )
            print("Изменения в портфеле:")
            print(f"- {currency}: было {prev_qty:.4f} → стало {new_qty:.4f}")
            print(f"Оценочная стоимость покупки: {cost:,.2f} USD")
        except ValueError as e:
            print(str(e))
        except KeyError as e:
            print(f"Ошибка данных: отсутствует поле {e}")
        except Exception as e:
            print(f"Не удалось выполнить покупку: {e}")

    def handle_sell(self, args: list[str]) -> None:
        if not self._is_logged_in():
            print(
                "Вы не вошли в систему. "
                "Выполните: login --username <имя пользователя> --password <пароль>"
            )            
            return

        try:
            currency = self._get_arg_value(args, '--currency')
            amount = self._get_arg_value(args, '--amount')
        except ValueError as e:
            print(str(e))

        if currency is None or amount is None:
            print("Ошибка: аргументы --currency и --amount обязательны.")
            return

        try:
            result = sell_currency(currency, amount)
            rate = result["rate"]
            revenue = result["revenue"]
            prev_qty = result.get("prev_qty", 0)
            new_qty = result["new_qty"]

            print(
                f"Продажа выполнена: {amount:.4f} {currency} "
                f"по курсу {rate:.2f} {currency}/USD"
            )
            print("Изменения в портфеле:")
            print(f"- {currency}: было {prev_qty:.4f} → стало {new_qty:.4f}")
            print(f"Оценочная выручка: {revenue:,.2f} USD")
        except ValueError as e:
            print(str(e))
        except KeyError as e:
            print(f"Ошибка данных: отсутствует поле {e}")
        except Exception as e:
            print(f"Не удалось выполнить продажу: {e}")

    def handle_get_rate(self, args: list[str]) -> None:
        try:
            from_cur = self._get_arg_value(args, '--from')
            to_cur = self._get_arg_value(args, '--to')
        except ValueError as e:
            print(str(e))
            
        if from_cur is None or to_cur is None:
            print("Ошибка: аргументы --from и --to обязательны.")
            return

        try:
            rate_info = get_rate(from_cur, to_cur)
            forward = rate_info["forward"]
            reverse = rate_info["reverse"]
            updated_at = rate_info["updated_at"]

            print(
                f"Курс {from_cur}→{to_cur}: {forward:.8f} "
                f"(обновлено: {updated_at})"
            )
            print(f"Обратный курс {to_cur}→{from_cur}: {reverse:.2f}")
        except ValueError as e:
            print(str(e))
        except KeyError as e:
            print(f"Ошибка данных курса: отсутствует поле {e}")
        except Exception as e:
            print(f"Не удалось получить курс: {e}")
