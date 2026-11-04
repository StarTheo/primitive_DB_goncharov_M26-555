import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.constants import META_FILE
from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    matches,
    select,
    update,
    validate_clause,
)
from primitive_db.parser import (
    parse_delete,
    parse_insert,
    parse_select,
    parse_update,
)
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    """Выводит список доступных команд."""
    print("Доступные команды:")
    print("help - показать справку")
    print("create_table <имя_таблицы> <столбец:тип> ... - создать таблицу")
    print("exit - выйти из программы")
    print(
        "update <таблица> set <столбец>=<значение> "
        "where <столбец>=<значение> - обновить записи"
    )
    print("info <имя_таблицы> - показать структуру и количество записей")
    print("delete from <таблица> where <столбец>=<значение> - удалить записи")
    print("drop_table <имя_таблицы> - удалить таблицу")
    print("list_tables - показать список всех таблиц")
    print("select from <имя_таблицы> [where <столбец> = <значение>] - показать записи")
    print("insert into <имя_таблицы> values (<значения>) - добавить запись")


def print_rows(schema, rows):
    """Выводит записи таблицы в порядке столбцов схемы."""
    table = PrettyTable()
    table.field_names = list(schema)

    for row in rows:
        values = []

        for column_name in schema:
            values.append(row[column_name])

        table.add_row(values)

    print(table)


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
        elif args[0] == "insert":
            try:
                table_name, values = parse_insert(command)
                metadata = load_metadata(META_FILE)
                rows = insert(metadata, table_name, values)
                save_table_data(table_name, rows)

                row_id = rows[-1]["ID"]
                print(
                    f'Запись с ID={row_id} успешно добавлена в таблицу "{table_name}".'
                )
            except ValueError as error:
                print(f"Ошибка: {error}")
        elif args[0] == "select":
            try:
                table_name, where_clause = parse_select(command)
                metadata = load_metadata(META_FILE)

                if table_name not in metadata:
                    raise ValueError(f'Таблица "{table_name}" не существует.')

                schema = metadata[table_name]
                validate_clause(schema, where_clause)

                rows = load_table_data(table_name)
                selected_rows = select(rows, where_clause)
                print_rows(schema, selected_rows)
            except ValueError as error:
                print(f"Ошибка: {error}")
        elif args[0] == "update":
            try:
                table_name, set_clause, where_clause = parse_update(command)
                metadata = load_metadata(META_FILE)

                if table_name not in metadata:
                    raise ValueError(f'Таблица "{table_name}" не существует.')

                schema = metadata[table_name]
                validate_clause(schema, where_clause)
                validate_clause(schema, set_clause, for_update=True)

                rows = load_table_data(table_name)
                affected_ids = []

                for row in rows:
                    if matches(row, where_clause):
                        affected_ids.append(row["ID"])

                updated_rows = update(rows, set_clause, where_clause)
                save_table_data(table_name, updated_rows)

                for row_id in affected_ids:
                    print(
                        f"Запись с ID={row_id} в таблице "
                        f'"{table_name}" успешно обновлена.'
                    )

                if not affected_ids:
                    print("Подходящие записи не найдены.")
            except ValueError as error:
                print(f"Ошибка: {error}")
        elif args[0] == "delete":
            try:
                table_name, where_clause = parse_delete(command)
                metadata = load_metadata(META_FILE)

                if table_name not in metadata:
                    raise ValueError(f'Таблица "{table_name}" не существует.')

                schema = metadata[table_name]
                validate_clause(schema, where_clause)

                rows = load_table_data(table_name)
                affected_ids = []

                for row in rows:
                    if matches(row, where_clause):
                        affected_ids.append(row["ID"])

                remaining_rows = delete(rows, where_clause)
                save_table_data(table_name, remaining_rows)

                for row_id in affected_ids:
                    print(
                        f"Запись с ID={row_id} успешно удалена "
                        f'из таблицы "{table_name}".'
                    )

                if not affected_ids:
                    print("Подходящие записи не найдены.")
            except ValueError as error:
                print(f"Ошибка: {error}")
        elif args[0] == "info":
            if len(args) != 2:
                print("Использование: info <имя_таблицы>")
                continue

            try:
                table_name = args[1]
                metadata = load_metadata(META_FILE)

                if table_name not in metadata:
                    raise ValueError(f'Таблица "{table_name}" не существует.')

                schema = metadata[table_name]
                descriptions = []

                for column_name, column_type in schema.items():
                    descriptions.append(f"{column_name}:{column_type}")

                columns_text = ", ".join(descriptions)
                rows = load_table_data(table_name)

                print(f"Таблица: {table_name}")
                print(f"Столбцы: {columns_text}")
                print(f"Количество записей: {len(rows)}")
            except ValueError as error:
                print(f"Ошибка: {error}")
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
