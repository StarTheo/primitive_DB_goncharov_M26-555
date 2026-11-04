import shlex

import prompt

from primitive_db.constants import META_FILE
from primitive_db.core import create_table, drop_table
from primitive_db.utils import load_metadata, save_metadata


def print_help():
    """Выводит список доступных команд."""
    print("Доступные команды:")
    print("create_table <имя_таблицы> <столбец:тип> ... - создать таблицу")
    print("exit - выйти из программы")
    print("drop_table <имя_таблицы> - удалить таблицу")
    print("list_tables - показать список всех таблиц")
    print("help - показать справку")


def welcome():
    """Обрабатывает команды до выхода пользователя."""
    print_help()

    while True:
        command = prompt.string("Введите команду: ").strip()

        try:
            args = shlex.split(command)
        except ValueError as error:
            print(f"Некорректная команда: {error}")
            continue

        if not args:
            continue

        if args[0] == "help":
            print_help()
        elif args[0] == "exit":
            print("До свидания!")
            break
        elif args[0] == "list_tables":
            if len(args) != 1:
                print("Использование: list_tables")
                continue

            metadata = load_metadata(META_FILE)

            if not metadata:
                print("В базе данных нет таблиц.")
            else:
                for table_name in metadata:
                    print(f"- {table_name}")
        elif args[0] == "create_table":
            if len(args) < 3:
                print("Использование: create_table <имя_таблицы> <столбец:тип> ...")
                continue

            metadata = load_metadata(META_FILE)

            try:
                table_name = args[1]
                create_table(metadata, table_name, args[2:])
                save_metadata(META_FILE, metadata)

                schema = metadata[table_name]
                descriptions = []

                for column_name, column_type in schema.items():
                    description = f"{column_name}:{column_type}"
                    descriptions.append(description)

                columns_text = ", ".join(descriptions)
                print(
                    f'Таблица "{table_name}" успешно создана '
                    f"со столбцами: {columns_text}"
                )
            except ValueError as error:
                print(f"Ошибка: {error}")
        elif args[0] == "drop_table":
            if len(args) != 2:
                print("Использование: drop_table <имя_таблицы>")
                continue

            metadata = load_metadata(META_FILE)
            table_name = args[1]

            try:
                drop_table(metadata, table_name)
                save_metadata(META_FILE, metadata)
                print(f'Таблица "{table_name}" успешно удалена.')
            except ValueError as error:
                print(f"Ошибка: {error}")
        else:
            print(f"Функции {args[0]} нет. Попробуйте снова.")
