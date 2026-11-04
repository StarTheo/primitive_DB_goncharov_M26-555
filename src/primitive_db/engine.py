import prompt


def print_help():
    """Выводит список доступных команд."""
    print("Доступные команды:")
    print("exit - выйти из программы")
    print("help - показать справку")


def welcome():
    """Обрабатывает команды до выхода пользователя."""
    print_help()

    while True:
        command = prompt.string("Введите команду: ").strip()

        if command == "help":
            print_help()
        elif command == "exit":
            print("До свидания!")
            break
        else:
            print(f"Функции {command} нет. Попробуйте снова.")