import prompt
import shlex

def run():
    while True:
        try:
            user_input = prompt.string('\n>>>Введите команду: ')
            args = shlex.split(user_input, posix=False)
            if len(args) == 0:
                continue
            
            command = args[0].lower()
            match command:
                case 'exit':
                    break
                case 'help':
                    print_help()
                case 'command':
                    pass

        except RuntimeError as e:
            print(f'Критичесая ошибка: {str(e)}')
            break

        # Все остальные ошибки
        except Exception as e:
            print('Произошла неизвестная ошибка. Попробуйте повторить '
                  f'операцию. {str(e)}')
            
def print_help() -> None:
    """Выводит справочную информацию"""
    print("*** Команды ***")