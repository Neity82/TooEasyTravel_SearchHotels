import re
from typing import Dict

import telebot
from decouple import config
from loguru import logger
from telebot import types

from log import logging_decor
from botrequests.city_class import City
from botrequests.hotel_class import Hotel


TOKEN: str = config("TOKEN")
KEY: str = config("KEY")

bot = telebot.TeleBot(TOKEN)

COMPANY: str = '"Too Easy Travel"'
URL_BASIC: str = "https://hotels4.p.rapidapi.com/"
HEADERS: Dict = {
    'x-rapidapi-key': KEY,
    'x-rapidapi-host': "hotels4.p.rapidapi.com"
}

user_requests: Dict = {}


@logging_decor
def new_user(chat_id: int) -> None:
    """
    Функция проверяет наличие id чата пользователя в словаре users по ключу.
    Если пользователя нет в словаре, то добавляет в словарь. Ключ - id чата, значение - создает инстанс класса City.
    """
    if chat_id not in user_requests:
        user_requests[chat_id] = City()
        logger.info("Новый пользователь добавлен в список, ID чата: {chat_id}".format(chat_id=chat_id))


@bot.message_handler(commands=['hello_world'])
@logging_decor
def hello_world(message: types.Message) -> None:
    """
    Функция обрабатывает команду /hello_world.
    Сначала вызывает функцию new_user, которая проверяет наличие id чата в
    словаре users. После выводит ответное сообщение пользователю.
    """
    new_user(message.chat.id)

    bot.send_message(message.from_user.id, "Привет Мир!")


@bot.message_handler(commands=['start'])
@logging_decor
def start_message(message: types.Message) -> None:
    """
    Функция обрабатывает команду /start.
    Сначала вызывает функцию new_user, которая проверяет наличие id чата в
    словаре users. Выводит стартовое сообщение пользователю.
    """
    new_user(message.chat.id)

    bot.send_message(message.from_user.id, "Привет, {user}! Я бот компании {name}. Я могу помочь Вам найти "
                                           "самые дешевые или самые дорогие отели по всему миру, "
                                           "подобрать наиболее подходящий для Вас отель по цене и расположению."
                                           "\n\nЧтобы узнать подробнее о моих возможностях - нажмите "
                                           "/help.".format(user=message.from_user.first_name,
                                                           name=COMPANY))


@bot.message_handler(commands=['help'])
@logging_decor
def help_message(message: types.Message) -> None:
    """
    Функция обрабатывает команду /help.
    Сначала вызывает функцию new_user, которая проверяет наличие id чата в
    словаре users. Выводит список команд пользователю.
    """
    new_user(message.chat.id)

    bot.send_message(message.from_user.id, "Бот {name} может:\n\n"
                                           "/lowprice - подобрать топ самых дешёвых отелей в городе\n"
                                           "/highprice - подобрать топ самых дорогих отелей в городе\n"
                                           "/bestdeal -подобрать топ отелей, наиболее подходящих по цене и "
                                           "расположению от центра(самые дешёвые и находятся ближе всего к "
                                           "центру)".format(name=COMPANY))


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
@logging_decor
@logger.catch
def commands(message: types.Message) -> None:
    """
    Функция обрабатывает запросы пользователя /lowprice, /highprice и /bestdeal.
    Сначала вызывает функцию new_user, которая проверяет наличие id чата в
    словаре users. Передает переменной sort_order инстанса класса City значение.
    """
    new_user(message.chat.id)
    if message.text.lower() == "/lowprice":
        user_requests[message.chat.id].sort_order = "PRICE"
    elif message.text.lower() == "/highprice":
        user_requests[message.chat.id].sort_order = "PRICE_HIGHEST_FIRST"
    elif message.text.lower() == "/bestdeal":
        user_requests[message.chat.id].sort_order = "DISTANCE_FROM_LANDMARK"
    query_city(message)


@logging_decor
@logger.catch
def query_city(message: types.Message) -> None:
    """
    Запрашивает у пользователя город для поиска.
    """
    bot.send_message(message.chat.id, "Введите название города")
    bot.register_next_step_handler(message, search_for_city)


@logging_decor
@logger.catch
def search_for_city(message: types.Message) -> None:
    """
    Поиск города

    Принимает на вход сообщение от пользователя с названием города, присваивает это значение переменной name
    инстанса класса City. Вызывает метод класса City для поиска всех городов с указанным названием, который возвращает
    словарь где ключ - id города, значение - название города, страна. Если найдено таких городов больше 1,
    то создается Inline клавиатуру с вариантами городов для выбора. Если возвращается пустой словарь, то вызывается
    исключение и пользователю сообщается, что такого города нет в БД.
    """

    user_requests[message.chat.id].name = message.text
    if not re.match(r"\b[а-я]\w*", message.text, flags=re.IGNORECASE):
        user_requests[message.chat.id].lang = "en_US"
    try:
        cities_list = user_requests[message.chat.id].search_all_id_for_name(URL_BASIC=URL_BASIC, HEADERS=HEADERS)
        if not cities_list:
            raise KeyError
        else:
            if len(cities_list) > 1:
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                key_list = [types.InlineKeyboardButton(text=i_name, callback_data=i_id)
                            for i_id, i_name in cities_list.items()]
                keyboard.add(*key_list)
                bot.send_message(message.chat.id, text="Выберите город из списка:", reply_markup=keyboard)
            else:
                user_requests[message.chat.id].city_id = [i_id for i_id in cities_list][0]
                query_total_hotels(message)
    except KeyError:
        logger.error("Город отсутствует в базе данных: {val}".format(val=message.text))
        bot.send_message(message.chat.id, "В моей базе нет такого города.")
        query_city(message)


@bot.callback_query_handler(func=lambda call: True)
@logging_decor
@logger.catch
def callback_worker(call: types.CallbackQuery) -> None:
    """
    Обработчик Inline клавиатуры.
    Принимает на вход значение callback_data и присваивает его переменной city_id инстанса класса City.
    После нажатия пользователем клавиатура убирается.
    """
    user_requests[call.message.chat.id].city_id = call.data
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    query_total_hotels(call.message)


@logging_decor
@logger.catch
def query_total_hotels(message: types.Message) -> None:
    """
    Функция запрашивает у пользователя какое количество отелей необходимо отобразить.
    """
    bot.send_message(message.chat.id, "Сколько отелей показать? (не более 25)")
    bot.register_next_step_handler(message, check_errors_in_total_hotels)


@logging_decor
@logger.catch
def check_errors_in_total_hotels(message: types.Message) -> None:
    """
    Функция обрабатывает ошибки, связанные с некорректным вводом количества отелей пользователем

    Получает на вход сообщение от пользователя с количеством отелей, проверяет, что это сообщение является числом и
    находится в допустимых границах (от 1 до 25). Если ввод не корректный, то выбрасывается исключение и пользователю
    сообщается, что либо нужно вводить числа, либо он вышел за границы допустимых значений.

    """
    try:
        if not message.text.isdigit():
            raise TypeError
        elif int(message.text) not in range(1, 26):
            raise ValueError
        else:
            user_requests[message.chat.id].total_hotels = message.text

    except TypeError:
        logger.error("Неверные формат ввода: {val}".format(val=message.text))
        bot.send_message(message.chat.id, "Вводите цифрами!")
        query_total_hotels(message)
    except ValueError:
        logger.error("Значение находится за пределами допустимого интервала: {val}".format(val=message.text))
        bot.send_message(message.chat.id, "Количество отелей не может быть меньше 1 и больше 25!")
        query_total_hotels(message)
    else:
        if user_requests[message.chat.id].sort_order == "DISTANCE_FROM_LANDMARK":
            query_min_max_price(message)
        else:
            choice_hotels(message)


@logging_decor
@logger.catch
def query_min_max_price(message: types.Message) -> None:
    """
    Запрашивает минимальную и максимальную стоимость отеля.
    """
    if len(user_requests[message.chat.id].min_max_price) == 0:
        bot.send_message(message.chat.id, "Введите минимальную стоимость отеля")
        bot.register_next_step_handler(message, check_errors_in_min_max_price)

    elif len(user_requests[message.chat.id].min_max_price) == 1:
        bot.send_message(message.chat.id, "Введите максимальную стоимость отеля")
        bot.register_next_step_handler(message, check_errors_in_min_max_price)

    else:
        query_distance(message)


@logging_decor
@logger.catch
def check_errors_in_min_max_price(message):
    """
    Функция обрабатывает ошибки, связанные с некорректным вводом стоимости отеля пользователем

    Принимает на вход сообщение о стоимости отеля от пользователя. Проверяет, что сообщение является числом.
    Если ввод не корректный выбрасывается исключение, пользователю сообщает о некорректном вводе.
    """
    try:
        if not message.text.isdigit():
            raise TypeError
    except TypeError:
        logger.error("Неверные формат ввода: {val}".format(val=message.text))
        bot.send_message(message.chat.id, "Вводите цифрами!")
        query_min_max_price(message)
    else:
        user_requests[message.chat.id].min_max_price.append(message.text)
        query_min_max_price(message)


@logging_decor
@logger.catch
def query_distance(message: types.Message) -> None:
    """
    Запрашивает минимальное и максимальное расстояние от отеля до центра.
    """
    if len(user_requests[message.chat.id].min_max_distance) == 0:
        bot.send_message(message.chat.id, "Введите минимальное расстояние от отеля до центра")
        bot.register_next_step_handler(message, check_errors_in_min_max_distance)

    elif len(user_requests[message.chat.id].min_max_distance) == 1:
        bot.send_message(message.chat.id, "Введите максимальное расстояние от отеля до центра")
        bot.register_next_step_handler(message, check_errors_in_min_max_distance)

    else:
        choice_hotels(message)


@logging_decor
@logger.catch
def check_errors_in_min_max_distance(message: types.Message) -> None:
    """
    Функция обрабатывает ошибки, связанные с некорректным вводом расстояния пользователем

    Принимает на вход сообщение о расстоянии от пользователя. Проверяет, что сообщение является числом.
    Если ввод не корректный выбрасывается исключение, пользователю сообщает о некорректном вводе.
        """
    try:
        if not message.text.isdigit():
            raise TypeError
    except TypeError:
        logger.error("Неверные формат ввода: {val}".format(val=message.text))
        bot.send_message(message.chat.id, "Вводите цифрами!")
        query_distance(message)
    else:
        user_requests[message.chat.id].min_max_distance.append(message.text)
        query_distance(message)


@logging_decor
@logger.catch
def choice_hotels(message: types.Message) -> None:
    """
    Подбор отелей по параметрам пользователя

    Вызывается метод класса City для подбора отелей, который возвращает список словарей с информацией по отелям.
    Из каждого объекта списка создается инстанс класса Hotel и добавляется в hotels класса City.
    Если возвращается пустой список, то выбрасывается исключение и пользователю сообщается, что по заданным параметрам
    отелей не найдено.

    """
    bot.send_message(message.chat.id, "Подбираю отели. Ожидайте...")
    hotels = user_requests[message.chat.id].search_hotels(URL_BASIC=URL_BASIC, HEADERS=HEADERS)
    for i_hotel in hotels:
        user_requests[message.chat.id].hotels.append(Hotel(all_info=i_hotel))
    try:
        if not user_requests[message.chat.id].hotels:
            raise ValueError

    except ValueError:
        logger.error("Отелей не найдено")
        bot.send_message(message.chat.id, "По вашему запросу ничего не найдено")
        user_requests.pop(message.chat.id)
    else:
        get_info(message)


@logging_decor
@logger.catch
def get_info(message: types.Message) -> None:
    """
    Передает информацию об отелях пользователю
    Из списка объектов класса Hotel формирует инфо и выдает в телеграмм пользователю.
    После список обнуляется.
    """
    for i_object in user_requests[message.chat.id].hotels:
        bot.send_message(chat_id=message.chat.id, text=i_object, parse_mode="Markdown")
    user_requests.pop(message.chat.id)


@bot.message_handler(content_types=['text'])
@logging_decor
def say_hello(message: types.Message) -> None:
    """
    Функция обрабатывает сообщения от пользователя (Привет, Спасибо) и
    отвечает на них соответствующей фразой
    """
    new_user(message.chat.id)

    if re.search(r"\bпривет\w*", message.text, flags=re.IGNORECASE):
        bot.send_message(message.chat.id, "Привет, чем я могу Вам помочь?\n\nЧтобы узнать подробнее о моих "
                                          "возможностях - нажмите /help.")
    elif re.search(r"\bспасибо\w*", message.text, flags=re.IGNORECASE):
        bot.send_message(message.chat.id, "Я рад, что смог Вам помочь!")
    else:
        bot.send_message(message.chat.id, "Я Вас не понимаю.\nЕсли хотите узнать, что я умею нажмите /help.")


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
