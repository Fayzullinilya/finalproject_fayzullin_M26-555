# valutatrade_hub\cli\interface.py
import shlex

import prompt

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.usecases import Auth, PortfolioService


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
            "update-rates": self.handle_update_rates,
            "show-rates": self.handle_show_rates,
            "help": self.handle_help,
        }
        self.user_auth = Auth()
        self.portfolio_service = PortfolioService()

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
                "Укажите одно значение."
            )
        return found_values[0]
    
    # ------------------------------------------------------------------
    # Основной цикл
    # ------------------------------------------------------------------

    def run(self) -> None:
        while True:
            try:
                # Временно передаем ID. поменяем на объект сессию и имя пользователя
                active_user = str(self._current_user_id) if self._is_logged_in else "Guest"
            
                user_input = prompt.string(f"\n<{active_user}> Введите команду: ")


                if user_input.strip().lower() == "exit":
                    break

                self.process_command(user_input)
            except (EOFError, KeyboardInterrupt):
                print("\nВыход из CLI.")
                break
            except Exception as e: # noqa: BLE001 — страховка цикла: выводим сообщение
                                   # в консоль и продолжаем работу
                print(f"Непредвиденная ошибка: {e}")

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
        print(" - update-rates [--source <coingecko/exchangerate>]")        

    def handle_register(self, args: list[str]) -> None:

        try:
            username = self._get_arg_value(args, '--username')
            password = self._get_arg_value(args, '--password')

            if username is None or password is None:
                print("Ошибка: аргументы --username и --password обязательны.")
                return

            username = username.strip()
            # пробелы в начале и конце пароля недопустимы
            password = password.strip()

            if not username or not password:
                print("Ошибка: имя и пароль не могут быть пустыми.")
                return

            user_id = self.user_auth.register_user(username, password)
            print(
                f"Пользователь '{username}' зарегистрирован (id={user_id}). "
                f"Войдите: login --username {username} --password ****"
            )
        except ValueError as e:
            print(f"Ошибка: {e!s}")
        except FileNotFoundError:
            print("Не удалось сохранить данные: файл базы не найден.")

    def handle_login(self, args: list[str]) -> None:
        try:
            username = self._get_arg_value(args, '--username')
            password = self._get_arg_value(args, '--password')

            if username is None or password is None:
                print("Ошибка: аргументы --username и --password обязательны.")
                return

            username = username.strip()
            # пробелы в начале и конце пароля недопустимы
            password = password.strip()

            if not username or not password:
                print("Ошибка: имя и пароль не могут быть пустыми.")
                return

            user_id = self.user_auth.login_user(username, password)
            self._set_current_user(user_id)
            print(f"Вы вошли как '{username}'.")
        except ValueError as e:
            print(f"Ошибка: {e!s}")

    def handle_show_portfolio(self, args: list[str]) -> None:
        if not self._is_logged_in():
            print(
                "Вы не вошли в систему. "
                "Выполните: login --username <имя пользователя> --password <пароль>"
            )            
            return

        try:
            base_currency = self._get_arg_value(args, '--base')

            data =self.portfolio_service.show_portfolio(self.current_user_id, base_currency)
            user = data.get("user", "")
            total = data.get("total", 0.0)
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
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e!s}")
        except KeyError as e:
            print(f"Ошибка данных портфеля: отсутствует поле {e}")
        except ValueError as e:
            print(str(e))

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

            if currency is None or amount is None:
                print("Ошибка: аргументы --currency и --amount обязательны.")
                return

            result = self.portfolio_service.buy_currency(self.current_user_id, currency, amount)
            rate = result["rate"]
            cost = result["cost"]
            prev_qty = result.get("prev_qty", 0)
            new_qty = result["new_qty"]

            print(
                f"Покупка выполнена: {int(amount):.4f} {currency} "
                f"по курсу {rate:.2f} {currency}/USD"
            )
            print("Изменения в портфеле:")
            print(f"- {currency}: было {prev_qty:.4f} → стало {new_qty:.4f}")
            print(f"Оценочная стоимость покупки: {cost:,.2f} USD")
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e!s}")
        except ValueError as e:
            print(str(e))
        except KeyError as e:
            print(f"Ошибка данных: отсутствует поле {e}")

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

            if currency is None or amount is None:
                print("Ошибка: аргументы --currency и --amount обязательны.")
                return

            result = self.portfolio_service.sell_currency(self.current_user_id, currency, amount)
            rate = result["rate"]
            revenue = result["revenue"]
            prev_qty = result.get("prev_qty", 0)
            new_qty = result["new_qty"]

            print(
                f"Продажа выполнена: {int(amount):.4f} {currency} "
                f"по курсу {rate:.2f} {currency}/USD"
            )
            print("Изменения в портфеле:")
            print(f"- {currency}: было {prev_qty:.4f} → стало {new_qty:.4f}")
            print(f"Оценочная выручка: {revenue:,.2f} USD")
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e!s}")
        except InsufficientFundsError as e:
            print(str(e))
        except ValueError as e:
            print(str(e))
        except KeyError as e:
            print(f"Ошибка данных: отсутствует поле {e}")

    def handle_get_rate(self, args: list[str]) -> None:
        """Обрабатывает команду get-rate --from <code> --to <code>."""
        try:
            from_currency = self._get_arg_value(args, "--from")
            to_currency = self._get_arg_value(args, "--to")

            # 1. Проверка: оба аргумента обязательны
            if not from_currency or not to_currency:
                print("Ошибка: укажите обе валюты. Пример: get-rate --from EUR --to BTC")
                return

            rate_result = self.portfolio_service.get_rate(from_currency, to_currency)

            if not rate_result["is_valid"]:
                missing = ", ".join(rate_result["missing"])
                print(f"Курс недоступен для валюты(й): {missing}")
                print("Подсказка: проверьте, загружен ли rates.json и есть ли там эти коды.")
                return

            print(f"Курс {rate_result['from']}→{rate_result['to']}: {rate_result['rate']:.8f}")
            print(f"Обратный курс {rate_result['to']}→{rate_result['from']}: {rate_result['inverse_rate']:.2f}")
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e!s}")
        except ValueError as e:
            print(str(e))
        except KeyError as e:
            print(f"Ошибка данных: отсутствует поле {e}")

    def handle_update_rates(self, args: list[str]) -> None:

        try:
            source = self._get_arg_value(args, '--source')
            if source is not None and source not in ("coingecko","exchangerate"):
                raise ValueError(
                    "Атрибут --source может принимать значения "
                    "coingecko / exchangerate"
                )
            result = self.portfolio_service.update_rates(source)

            for name, count in result["ok"].items():
                print(f"INFO: Получение курсов от {name}... OK ({count} курсов)")
            for name, err in result["failed"].items():
                print(f"ОШИБКА: Не удалось получить данные от {name}: {err}")

            print(f"INFO: Запись {result['total']} курсов в data/rates.json...")

            if result["failed"]:
                print("Обновление завершено с ошибками. Подробности в logs/parser.log.")
            else:
                print(f"Обновление успешно. Всего обновлено курсов: {result['total']}. "
                    f"Последнее обновление: {result['last_refresh']}")

        except ApiRequestError as e:
            print(f"Ошибка: {e!s}")
        except ValueError as e:
            print(f"Ошибка: {e!s}")

    def handle_show_rates(self, args) -> None:
        try:
            currency = self._get_arg_value(args, '--currency')
            top = self._get_arg_value(args, '--top')
            base = self._get_arg_value(args, '--base')

            # Валидация
            if top is not None:
                top = int(top)
                if top <= 0:
                    raise ValueError("Аргумент --top должен быть положительным целым числом.")
            for name, value in (("--currency", currency), ("--base", base)):
                if value is not None and not value.isalpha():
                    raise ValueError(f"Аргумент {name} должен быть кодом валюты, например BTC или EUR.")

            result = self.portfolio_service.show_rates(currency=currency, top=top, base=base)

            # Вывод
            print(f"Rates from cache (updated at {result['last_refresh']}):")
            for row in result["rows"]:
                print(f"- {row['pair']}: {row['rate']:.4f}")
        
        except (ValueError, CurrencyNotFoundError) as e:
            print(f"Ошибка: {e}")
            return 