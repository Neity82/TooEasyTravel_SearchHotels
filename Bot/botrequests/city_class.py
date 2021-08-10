import json
import datetime
from typing import Dict

import requests

from Bot.log import logging_decor, logging_decor_cls


@logging_decor_cls
class City:
    """
    Класс City содержит параметры запроса пользователя по городу

    Args:
        name (str): передается название города
        city_id (str): передается идентификатор города
        sort_order (str): передается параметр поиска
        total_hotels (str): передается количество отелей для отображения пользователю
        info_hotels (Dict): передается словарь с отелями

    Attributes:
        _name (str): название города
        _city_id (str): идентификатор города
        _sort_order (str): параметр поиска
        _total_hotels (str): количество отелей для отображения пользователю
        _info_hotels (Dict): словарь с отелями

    """

    def __init__(self, name=None, city_id=None, sort_order=None, total_hotels=None, info_hotels=None) -> None:
        if info_hotels is None:
            info_hotels = []
        self._name = name
        self._city_id = city_id
        self._sort_order = sort_order
        self._total_hotels = total_hotels
        self._info_hotels = info_hotels

    @property
    def name(self):
        return self._name

    @property
    def city_id(self):
        return self._city_id

    @property
    def sort_order(self):
        return self._sort_order

    @property
    def total_hotels(self):
        return self._total_hotels

    @property
    def info_hotels(self):
        return self._info_hotels

    @name.setter
    def name(self, name):
        self._name = name

    @city_id.setter
    def city_id(self, city_id):
        self._city_id = city_id

    @sort_order.setter
    def sort_order(self, sort_order):
        self._sort_order = sort_order

    @total_hotels.setter
    def total_hotels(self, total_hotels):
        self._total_hotels = total_hotels

    @info_hotels.setter
    def info_hotels(self, info_hotels):
        self._info_hotels = info_hotels

    @logging_decor
    def search_all_id_for_name(self, URL_BASIC: str, HEADERS: Dict) -> Dict:
        """
        Создает запрос на API Hotels по имени города. Полученные данные записывает в словарь:
        key - идентификатор города, value - название города и страна
        Возвращает словарь

        :param URL_BASIC:
        :type URL_BASIC: str
        :param HEADERS:
        :type HEADERS: Dict
        :return: cities
        :rtype: Dict
        """

        cities = dict()
        url = URL_BASIC + "locations/search"
        querystring = {"query": self._name, "locale": "ru_RU"}

        response = requests.request("GET", url, headers=HEADERS, params=querystring)
        data = json.loads(response.text)
        for i_elem in data["suggestions"][0]["entities"]:
            if i_elem.get("type") == "CITY" and i_elem.get("name") == self._name.title():
                city_id = i_elem.get("destinationId")
                name = self._name.title() + ", " + i_elem.get("caption").split("</span>, ")[-1]
                cities[city_id] = name
        return cities

    @logging_decor
    def search_hotels(self, URL_BASIC: str, HEADERS: Dict) -> Dict:
        """
        Создает запрос на API Hotels для поиска отелей в городе.

        :param URL_BASIC:
        :type URL_BASIC: str
        :param HEADERS:
        :type HEADERS: Dict
        :return: hotels
        :rtype: Dict
        """

        url = URL_BASIC + "properties/list"
        check_in = datetime.datetime.now().strftime("%Y-%m-%d")
        check_out = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        querystring = {"adults1": "1", "pageNumber": "1", "destinationId": self._city_id,
                       "pageSize": self._total_hotels, "checkOut": check_out, "checkIn": check_in,
                       "sortOrder": self._sort_order, "locale": "ru_RU", "currency": "RUB"}

        response = requests.request("GET", url, headers=HEADERS, params=querystring)
        hotels = json.loads(response.text)
        print(hotels)
        return hotels
