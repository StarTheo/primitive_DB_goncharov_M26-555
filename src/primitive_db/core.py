"""Основная логика управления таблицами."""

from primitive_db.constants import VALID_TYPES
from primitive_db.utils import delete_table_data, load_table_data


def create_table(metadata, table_name, columns):
    """Проверяет столбцы и добавляет новую таблицу в метаданные."""
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}.")

    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')

    if not columns:
        raise ValueError("Укажите хотя бы один столбец.")

    schema = {"ID": "int"}
    seen_columns = set()

    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            raise ValueError(f"Некорректное описание столбца: {column}.")

        column_name, column_type = parts

        if not column_name.isidentifier():
            raise ValueError(f"Некорректное имя столбца: {column_name}.")

        if column_name in seen_columns:
            raise ValueError(f"Повторяющийся столбец: {column_name}.")

        if column_type not in VALID_TYPES:
            raise ValueError(f"неподдерживаемый тип: {column_type}.")

        if column_name == "ID" and column_type != "int":
            raise ValueError("Столбец ID должен иметь тип int.")

        schema[column_name] = column_type
        seen_columns.add(column_name)

    metadata[table_name] = schema
    return metadata


def drop_table(metadata, table_name):
    """Удаляет файл данных таблицы и её схему."""
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    delete_table_data(table_name)
    del metadata[table_name]
    return metadata


def validate_value(column_name, column_type, value):
    """Проверяет соответствие значения типу столбца."""
    actual_type = type(value).__name__

    if actual_type != column_type:
        raise ValueError(
            f'Столбец "{column_name}" ожидает {column_type}, получено {actual_type}.'
        )


def insert(metadata, table_name, values):
    """Проверяет значения и возвращает записи с добавленной строкой."""
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    schema = metadata[table_name]
    columns = list(schema)[1:]

    if len(values) != len(columns):
        raise ValueError(
            f"Ожидается значений: {len(columns)}, получено: {len(values)}."
        )

    for column_name, value in zip(columns, values):
        column_type = schema[column_name]
        validate_value(column_name, column_type, value)

    rows = load_table_data(table_name)
    ids = []

    for row in rows:
        ids.append(row["ID"])

    new_id = max(ids, default=0) + 1
    new_row = {"ID": new_id}

    for column_name, value in zip(columns, values):
        new_row[column_name] = value

    rows.append(new_row)
    return rows


def matches(row, where_clause):
    """Проверяет соответствие записи условию."""
    for column_name, value in where_clause.items():
        if row[column_name] != value:
            return False

    return True


def select(table_data, where_clause=None):
    """Возвращает все записи или записи, соответствующие условию."""
    selected_rows = []

    for row in table_data:
        if where_clause is None or matches(row, where_clause):
            selected_rows.append(row.copy())

    return selected_rows


def validate_clause(schema, clause, for_update=False):
    """Проверяет столбцы и типы, запрещает изменение ID."""
    if clause is None:
        return

    for column_name, value in clause.items():
        if column_name not in schema:
            raise ValueError(f'Столбец "{column_name}" не существует.')

        if for_update and column_name == "ID":
            raise ValueError("Изменение ID запрещено.")

        validate_value(column_name, schema[column_name], value)


def update(table_data, set_clause, where_clause):
    """Изменяет поля записей, соответствующих условию."""
    for row in table_data:
        if matches(row, where_clause):
            row.update(set_clause)

    return table_data


def delete(table_data, where_clause):
    """Возвращает записи, не соответствующие условию удаления."""
    remaining_rows = []

    for row in table_data:
        if not matches(row, where_clause):
            remaining_rows.append(row)

    return remaining_rows
