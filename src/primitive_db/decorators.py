"""Декораторы и замыкания приложения."""

import time


def handle_db_errors(function):
    """Перехватывает ошибки операции и выводит понятное сообщение."""

    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден.")
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except ValueError as error:
            print(f"Ошибка: {error}")
        except Exception as error:
            print(f"Произошла непредвиденная ошибка: {error}")

        return None

    wrapper.__name__ = function.__name__
    wrapper.__doc__ = function.__doc__
    return wrapper


def confirm_action(action_name):
    """Создаёт декоратор подтверждения указанного действия."""

    def decorate(function):
        def wrapper(*args, **kwargs):
            answer = input(f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ')

            if answer.strip() != "y":
                print("Операция отменена.")
                return None

            return function(*args, **kwargs)

        wrapper.__name__ = function.__name__
        wrapper.__doc__ = function.__doc__
        return wrapper

    return decorate


def log_time(function):
    """Измеряет время выполнения функции и возвращает её результат."""

    def wrapper(*args, **kwargs):
        started_at = time.monotonic()
        result = function(*args, **kwargs)
        elapsed = time.monotonic() - started_at

        print(f"Функция {function.__name__} выполнилась за {elapsed:.3f} секунд")
        return result

    wrapper.__name__ = function.__name__
    wrapper.__doc__ = function.__doc__
    return wrapper


def create_cacher():
    """Создаёт функцию доступа к кэшу в замыкании."""
    cache = {}

    def cache_result(key, value_func):
        if key not in cache:
            value = value_func()

            if value is not None:
                cache[key] = value

            return value

        return cache[key]

    return cache_result
