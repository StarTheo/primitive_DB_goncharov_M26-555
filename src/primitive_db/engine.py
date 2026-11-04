"""Ввод команд, вывод результатов и управление сеансом."""

import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.constants import META_FILE, STATUS_CHANGED, STATUS_EXIT
from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    matches,
    require_table,
    select,
    update,
    validate_clause,
)
from primitive_db.decorators import create_cacher, handle_db_errors
from primitive_db.parser import parse_delete, parse_insert, parse_select, parse_update
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


def make_select_key(table_name, where_clause):
    """Создаёт ключ кэша из имени таблицы и условия."""
    if where_clause is None:
        return (table_name, None)
    conditions = []
    for column_name, value in sorted(where_clause.items()):
        conditions.append((column_name, type(value).__name__, value))
    return (table_name, tuple(conditions))


@handle_db_errors
def execute_command(command, cache_result):
    """Выполняет одну команду и возвращает статус."""
    args = shlex.split(command)
    if not args:
        return
    if args[0] == "help":
        print_help()
    elif args[0] == "exit":
        print("До свидания!")
        return STATUS_EXIT
    elif args[0] == "list_tables":
        if len(args) != 1:
            print("Использование: list_tables")
            return
        metadata = load_metadata(META_FILE)
        if not metadata:
            print("В базе данных нет таблиц.")
        else:
            for table_name in metadata:
                print(f"- {table_name}")
    elif args[0] == "insert":
        table_name, values = parse_insert(command)
        metadata = load_metadata(META_FILE)
        rows = insert(metadata, table_name, values)
        if rows is None:
            return
        save_table_data(table_name, rows)
        row_id = rows[-1]["ID"]
        print(f'Запись с ID={row_id} успешно добавлена в таблицу "{table_name}".')
        return STATUS_CHANGED
    elif args[0] == "select":
        table_name, where_clause = parse_select(command)
        metadata = load_metadata(META_FILE)
        schema = require_table(metadata, table_name)
        validate_clause(schema, where_clause)
        cache_key = make_select_key(table_name, where_clause)

        def fetch_rows():
            """Читает и фильтрует записи при отсутствии результата в кэше."""
            rows = load_table_data(table_name)
            return select(rows, where_clause)

        selected_rows = cache_result(cache_key, fetch_rows)
        if selected_rows is None:
            return
        print_rows(schema, selected_rows)
    elif args[0] == "update":
        table_name, set_clause, where_clause = parse_update(command)
        metadata = load_metadata(META_FILE)
        schema = require_table(metadata, table_name)
        validate_clause(schema, where_clause)
        validate_clause(schema, set_clause, for_update=True)
        rows = load_table_data(table_name)
        affected_ids = []
        for row in rows:
            if matches(row, where_clause):
                affected_ids.append(row["ID"])
        updated_rows = update(rows, set_clause, where_clause)
        if updated_rows is None:
            return
        save_table_data(table_name, updated_rows)
        for row_id in affected_ids:
            print(f'Запись с ID={row_id} в таблице "{table_name}" успешно обновлена.')
        if not affected_ids:
            print("Подходящие записи не найдены.")
        return STATUS_CHANGED
    elif args[0] == "delete":
        table_name, where_clause = parse_delete(command)
        metadata = load_metadata(META_FILE)
        schema = require_table(metadata, table_name)
        validate_clause(schema, where_clause)
        rows = load_table_data(table_name)
        affected_ids = []
        for row in rows:
            if matches(row, where_clause):
                affected_ids.append(row["ID"])
        remaining_rows = delete(rows, where_clause)
        if remaining_rows is None:
            return
        save_table_data(table_name, remaining_rows)
        for row_id in affected_ids:
            print(f'Запись с ID={row_id} успешно удалена из таблицы "{table_name}".')
        if not affected_ids:
            print("Подходящие записи не найдены.")
        return STATUS_CHANGED
    elif args[0] == "info":
        if len(args) != 2:
            print("Использование: info <имя_таблицы>")
            return
        table_name = args[1]
        metadata = load_metadata(META_FILE)
        schema = require_table(metadata, table_name)
        descriptions = []
        for column_name, column_type in schema.items():
            descriptions.append(f"{column_name}:{column_type}")
        columns_text = ", ".join(descriptions)
        rows = load_table_data(table_name)
        print(f"Таблица: {table_name}")
        print(f"Столбцы: {columns_text}")
        print(f"Количество записей: {len(rows)}")
    elif args[0] == "create_table":
        if len(args) < 3:
            print("Использование: create_table <имя_таблицы> <столбец:тип> ...")
            return
        metadata = load_metadata(META_FILE)
        table_name = args[1]
        result = create_table(metadata, table_name, args[2:])
        if result is None:
            return
        save_metadata(META_FILE, metadata)
        schema = metadata[table_name]
        descriptions = []
        for column_name, column_type in schema.items():
            description = f"{column_name}:{column_type}"
            descriptions.append(description)
        columns_text = ", ".join(descriptions)
        print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_text}')
        return STATUS_CHANGED
    elif args[0] == "drop_table":
        if len(args) != 2:
            print("Использование: drop_table <имя_таблицы>")
            return
        metadata = load_metadata(META_FILE)
        table_name = args[1]
        if table_name not in metadata:
            raise ValueError(f'Таблица "{table_name}" не существует.')
        result = drop_table(metadata, table_name)
        if result is None:
            return
        save_metadata(META_FILE, result)
        print(f'Таблица "{table_name}" успешно удалена.')
        return STATUS_CHANGED
    else:
        print(f"Функции {args[0]} нет. Попробуйте снова.")


def welcome():
    """Запрашивает команды, управляет выходом и сбросом кэша."""
    print_help()
    cache_result = create_cacher()
    while True:
        try:
            command = prompt.string("Введите команду: ").strip()
            status = execute_command(command, cache_result)
        except (EOFError, KeyboardInterrupt):
            print("\nДо свидания!")
            break
        if status == STATUS_EXIT:
            break
        if status == STATUS_CHANGED:
            cache_result = create_cacher()
