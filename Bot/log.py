import os
import functools
from typing import Callable

from loguru import logger

path_log: str = os.sep.join(("logs", "logging_{time}.log"))
logger.add(path_log, format="{time} | {level}   | {message}", level="DEBUG", encoding="utf-8")


def logging_decor(func: Callable) -> Callable:
    """
    Функция декоратор, записывает в файл 'logging.log' о вызове функции.
    Передает в файл название функции и аргументы
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug("Вызвана функция: {func}, аргументы: {args}, {kwargs}".format(func=func.__name__,
                                                                                   args=args, kwargs=kwargs))
        if args:
            for info in args:
                logger.info(info)
        if kwargs:
            for info in kwargs:
                logger.info(info)

        result = func(*args, **kwargs)
        return result

    return wrapper


def logging_decor_cls(cls):
    """
    Функция декоратор класса, записывает в файл 'logging.log' о создании инстанса класса.
    Передает в файл название класса и переданные аргументы
    """

    @functools.wraps(cls)
    def wrapper(*args, **kwargs):
        logger.debug("Создан инстанс класса: {cls}, аргументы: {args}, {kwargs}".format(cls=cls.__name__,
                                                                                        args=args, kwargs=kwargs))
        instance = cls(*args, **kwargs)
        return instance

    return wrapper


