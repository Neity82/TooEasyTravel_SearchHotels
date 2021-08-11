import json
import datetime
from typing import Dict, List

import requests

from Bot.log import logging_decor, logging_decor_cls


@logging_decor_cls
class City:
    """
    Класс City содержит параметры запроса пользователя по городу

    Args:
        name (str): передается название города
        lang (str): передается язык ввода
        city_id (str): передается идентификатор города
        sort_order (str): передается параметр поиска
        total_hotels (str): передается количество отелей для отображения пользователю
        hotels (List): передается список с инстансами класса Hotel
        min_max_price (List[str]): передается минимальная цена за ночь для функции bestdeal
        min_max_distance (List[str]): передается минимальное и максимальное расстояние
                                        от центра до отеля для функции bestdeal

    Attributes:
        _name (str): название города
        _lang (str): язык ввода
        _city_id (str): идентификатор города
        _sort_order (str): параметр поиска
        _total_hotels (str): количество отелей для отображения пользователю
        _hotels (List): список с инстансами класса Hotel
        _min_max_price (List[str]): минимальная и максимальная цена за ночь для функции bestdeal
        _min_max_distance (List[str]): минимальное и максимальное расстояние от центра до отеля для функции bestdeal

    """

    def __init__(self, name: str = None, lang: str = "ru_RU", city_id: str = None, sort_order: str = None,
                 total_hotels: str = None, hotels: List = None, min_max_price: List[str] = None,
                 min_max_distance: List[str] = None) -> None:
        if hotels is None:
            hotels = []
        if min_max_price is None:
            min_max_price = []
        if min_max_distance is None:
            min_max_distance = []
        self._name = name
        self._lang = lang
        self._city_id = city_id
        self._sort_order = sort_order
        self._total_hotels = total_hotels
        self._hotels = hotels
        self._min_max_price = min_max_price
        self._min_max_distance = min_max_distance

    @property
    def name(self) -> str:
        return self._name

    @property
    def lang(self) -> str:
        return self._lang

    @property
    def city_id(self) -> str:
        return self._city_id

    @property
    def sort_order(self) -> str:
        return self._sort_order

    @property
    def total_hotels(self) -> str:
        return self._total_hotels

    @property
    def hotels(self) -> List:
        return self._hotels

    @property
    def min_max_price(self) -> List:
        return self._min_max_price

    @property
    def min_max_distance(self) -> List:
        return self._min_max_distance

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

    @lang.setter
    def lang(self, lang: str) -> None:
        self._lang = lang

    @city_id.setter
    def city_id(self, city_id: str) -> None:
        self._city_id = city_id

    @sort_order.setter
    def sort_order(self, sort_order: str) -> None:
        self._sort_order = sort_order

    @total_hotels.setter
    def total_hotels(self, total_hotels: str) -> None:
        self._total_hotels = total_hotels

    @hotels.setter
    def hotels(self, hotels: List) -> None:
        self._hotels = hotels

    @min_max_price.setter
    def min_max_price(self, min_max_price: List[str]) -> None:
        self._min_max_price = min_max_price

    @min_max_distance.setter
    def min_max_distance(self, min_max_distance: List[str]) -> None:
        self._min_max_distance = min_max_distance

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
        querystring = {"query": self._name, "locale": self._lang}

        response = requests.request("GET", url, headers=HEADERS, params=querystring)
        data = json.loads(response.text)
        for i_elem in data["suggestions"][0]["entities"]:
            if i_elem.get("type") == "CITY" and i_elem.get("name") == self._name.title():
                city_id = i_elem.get("destinationId")
                name = self._name.title() + ", " + i_elem.get("caption").split("</span>, ")[-1]
                cities[city_id] = name
        return cities

    @logging_decor
    def search_hotels(self, URL_BASIC: str, HEADERS: Dict) -> List:
        """
        Создает запрос на API Hotels для поиска отелей в указанном городе.
        Возвращает список словарей с информацией об отелях.

        :param URL_BASIC:
        :type URL_BASIC: str

        :param HEADERS:
        :type HEADERS: Dict

        :return: hotels
        :rtype: List
        """

        url = URL_BASIC + "properties/list"
        check_in = datetime.datetime.now().strftime("%Y-%m-%d")
        check_out = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        if self._sort_order != "DISTANCE_FROM_LANDMARK":
            querystring = {"adults1": "1", "pageNumber": "1", "destinationId": self._city_id,
                           "pageSize": self._total_hotels, "checkOut": check_out, "checkIn": check_in,
                           "sortOrder": self._sort_order, "locale": self._lang, "currency": "RUB"}

            response = requests.request("GET", url, headers=HEADERS, params=querystring)
            hotels = json.loads(response.text)
            return hotels.get("data", {}).get("body", {}).get("searchResults", {}).get("results", '')

        else:
            hotels = list()
            page_number = 1
            min_distance = min(list(map(lambda x: float(x), self._min_max_distance)))
            max_distance = max(list(map(lambda x: float(x), self._min_max_distance)))
            search = True

            while search:
                querystring = {"adults1": "1", "pageNumber": str(page_number), "destinationId": self._city_id,
                               "pageSize": 25, "checkOut": check_out, "checkIn": check_in,
                               "priceMax": max(self._min_max_price), "sortOrder": self._sort_order,
                               "locale": self._lang, "currency": "RUB", "priceMin": min(self._min_max_price)}
                response = requests.request("GET", url, headers=HEADERS, params=querystring)
                interim_hotels = json.loads(response.text)

                for i_hotels in interim_hotels.get("data", {}).get("body", {}).get("searchResults", {}).get("results", ''):
                    distance = i_hotels["landmarks"][0]["distance"].replace(',', '.').split()[0]
                    if float(distance) > max_distance:
                        search = False
                        break
                    if float(distance) >= min_distance:
                        hotels.append(i_hotels)
                if len(interim_hotels.get("data", {}).get("body", {}).get("searchResults", {}).get("results", '')) < 25:
                    break
                page_number += 1

            hotels = sorted(hotels, key=lambda x: x["ratePlan"]["price"]["exactCurrent"])
            return hotels[:int(self._total_hotels)]


