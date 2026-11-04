"""Разбор команд и значений пользователя."""

import shlex


def parse_value(text):
    """Преобразует текст одного значения в str, bool или int."""
    text = text.strip()

    if not text:
        raise ValueError("Не указано значение.")

    if text[0] in ("'", '"'):
        parts = shlex.split(text)

        if len(parts) != 1:
            raise ValueError("Ожидается одно строковое значение.")

        return parts[0]

    if text.lower() == "true":
        return True

    if text.lower() == "false":
        return False

    try:
        return int(text)
    except ValueError:
        raise ValueError(f"Некорректное значение: {text}. Строки нужны в кавычках.")


def parse_values(text):
    """Разбирает значения, разделённые запятыми вне кавычек."""
    if not text.strip():
        return []

    lexer = shlex.shlex(text, posix=False, punctuation_chars=",")
    lexer.whitespace_split = True
    lexer.commenters = ""

    values = []
    expect_value = True

    for token in lexer:
        if expect_value:
            values.append(parse_value(token))
        else:
            if token != ",":
                raise ValueError("Между значениями нужна запятая.")

        expect_value = not expect_value

    if expect_value:
        raise ValueError("После запятой требуется значение.")

    return values


def parse_insert(command):
    """Извлекает имя таблицы и значения из команды insert."""
    parts = command.split(maxsplit=4)

    if len(parts) != 5:
        raise ValueError("Использование: insert into <имя_таблицы> values (<значения>)")

    if parts[0] != "insert" or parts[1] != "into" or parts[3] != "values":
        raise ValueError("Ожидается команда insert into <имя_таблицы> values (...).")

    table_name = parts[2]
    values_text = parts[4].strip()

    if not values_text.startswith("(") or not values_text.endswith(")"):
        raise ValueError("Значения должны быть заключены в круглые скобки.")

    values = parse_values(values_text[1:-1])
    return table_name, values


def parse_where(text):
    """Разбирает одно условие равенства в словарь."""
    column_name, separator, value_text = text.partition("=")

    if not separator:
        raise ValueError("В условии требуется знак =.")

    column_name = column_name.strip()

    if not column_name.isidentifier():
        raise ValueError(f"Некорректное имя столбца: {column_name}.")

    value = parse_value(value_text)
    return {column_name: value}


def parse_select(command):
    """Извлекает имя таблицы и необязательное условие выборки."""
    parts = command.split(maxsplit=4)

    if len(parts) < 3 or parts[0] != "select" or parts[1] != "from":
        raise ValueError("Использование: select from <имя_таблицы> [where <условие>]")

    table_name = parts[2]

    if len(parts) == 3:
        return table_name, None

    if len(parts) != 5 or parts[3] != "where":
        raise ValueError("После имени таблицы ожидается where <столбец> = <значение>.")

    where_clause = parse_where(parts[4])
    return table_name, where_clause


def tokenize(command):
    """Разбивает команду на слова, знаки и строки в кавычках."""
    lexer = shlex.shlex(command, posix=False, punctuation_chars="=,()")
    lexer.whitespace_split = True
    lexer.commenters = ""

    return list(lexer)


def parse_set(tokens, position):
    """Разбирает присваивания и возвращает позицию следующей части команды."""
    changes = {}

    while True:
        if position + 2 >= len(tokens):
            raise ValueError("После set требуется столбец = значение.")

        column_name = tokens[position]

        if not column_name.isidentifier():
            raise ValueError(f"Некорректное имя столбца: {column_name}.")

        if tokens[position + 1] != "=":
            raise ValueError("После имени столбца требуется знак =.")

        if column_name in changes:
            raise ValueError(f"Повторяющийся столбец: {column_name}.")

        changes[column_name] = parse_value(tokens[position + 2])
        position += 3

        if position == len(tokens) or tokens[position] != ",":
            break

        position += 1

    return changes, position


def parse_update(command):
    """Извлекает таблицу, изменения и условие команды update."""
    tokens = tokenize(command)

    if len(tokens) < 3 or tokens[0] != "update" or tokens[2] != "set":
        raise ValueError(
            "Использование: update <таблица> set <изменения> where <условие>"
        )

    table_name = tokens[1]
    set_clause, position = parse_set(tokens, 3)

    if position >= len(tokens) or tokens[position] != "where":
        raise ValueError("После изменений требуется условие where.")

    where_tokens = tokens[position + 1 :]

    if len(where_tokens) != 3 or where_tokens[1] != "=":
        raise ValueError("Условие должно иметь вид: столбец = значение.")

    where_text = " ".join(where_tokens)
    where_clause = parse_where(where_text)

    return table_name, set_clause, where_clause


def parse_delete(command):
    """Извлекает таблицу и обязательное условие удаления."""
    parts = command.split(maxsplit=4)

    if len(parts) != 5:
        raise ValueError("Использование: delete from <таблица> where <условие>")

    if parts[0] != "delete" or parts[1] != "from" or parts[3] != "where":
        raise ValueError("Ожидается delete from <таблица> where <условие>.")

    return parts[2], parse_where(parts[4])
