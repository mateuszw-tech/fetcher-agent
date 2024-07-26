import concurrent
import json
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import List

from bs4 import BeautifulSoup
import asyncio
import aiohttp
import socket
from utils import SprzedajemyUtils, ScraperUtils


class AdvertisementInfo:

    def __init__(
            self,
            title: str,
            username: str,
            location: str,
            phone_number: str,
            price: str,
            url: str,
    ):
        self.title = title
        self.username = username
        self.location = location
        self.phone_number = phone_number
        self.price = price
        self.url = url

    def convert_to_json(self) -> str:
        info_dict = {
            "title": self.title,
            "username": self.username,
            "location": self.location,
            "phone_number": self.phone_number,
            "price": self.price,
            "url": self.url,
        }
        return json.dumps(info_dict)


class Fetcher(ABC):
    @abstractmethod
    def collect_osint_data(self, offer_list) -> List[AdvertisementInfo]:
        raise NotImplementedError()

    @abstractmethod
    def start(self, host: str, port: int, client_socket: socket.socket) -> None:
        raise NotImplementedError()

    @abstractmethod
    @property
    def settings(self):
        raise NotImplementedError()


class SprzedajemyFetcher(Fetcher):  # NOQA

    def __init__(self, *cities: str):
        self.cities: tuple = cities
        self.collected_osint_data: list[AdvertisementInfo] = []
    # Fetcher ma wkładać rzeczy do kolejki, agent niech z niej wyciąga, wszystko pojedynczo
    # pool, kolejka ma być bezpieczna pomiędzy wątkami (thread safe)
    # zbieram OLAP nie OLTP,

    def get_all_offers_urls(self) -> List[str]:
        pages = ScraperUtils.get_all_pages_urls_from_different_cities(
            SprzedajemyUtils.get_all_pages_urls, *self.cities
        )
        advertisement_urls_futures = []
        collected_lists_of_advertisement_urls = []
        with ThreadPoolExecutor(max_workers=16) as executor:

            for page in pages:
                advertisement_urls_futures.append(
                    executor.submit(SprzedajemyUtils.find_all_offers_in_current_page, page)
                )

            completed_futures, _ = concurrent.futures.wait(advertisement_urls_futures)
            for future in completed_futures:
                collected_lists_of_advertisement_urls.append(future.result())

            advertisement_urls = [
                advertisement_url
                for advertisements_list_from_single_page in collected_lists_of_advertisement_urls
                for advertisement_url in advertisements_list_from_single_page
            ]

        return advertisement_urls

    async def append_data(self, info: AdvertisementInfo) -> None:
        self.collected_osint_data.append(info)

    async def load_advertisement_info_from_url(self, advertisement_url: str):
        try:
            async with aiohttp.ClientSession(
                    trust_env=True, timeout=aiohttp.ClientTimeout(total=20)
            ) as session:
                async with session.get(advertisement_url, timeout=25) as resp:
                    body: str = await resp.text()
                    soup: BeautifulSoup = BeautifulSoup(body, "html.parser")
                    title, username, location, phone_number, price = SprzedajemyUtils.get_offer_details(soup)
            await self.append_data(
                AdvertisementInfo(title, username, location, phone_number, price, advertisement_url)
            )
        except Exception as e:
            print({e})
            raise Exception

    async def collect_osint_data(self, offer_list: list[str]) -> None:
        tasks = []
        for offer in offer_list:
            task = asyncio.create_task(
                ScraperUtils.fail_repeat_execution(self.load_advertisement_info_from_url, offer)
            )
            tasks.append(task)

        await asyncio.gather(*tasks)

    def change_cities(self, *cities: str) -> None:
        self.cities = cities

    @staticmethod
    def send_data_to_server(
            host: str, port: int, client_socket: socket.socket, info_list: list
    ) -> None:
        json_data = json.dumps(info_list)
        with client_socket as s:
            s.connect((host, port))
            s.sendall(bytes(json_data, encoding="utf-8"))
            print(f"Sent JSON data: {json_data}")
            s.close()

    def start(self, host: str, port: int, client_socket: socket.socket) -> None:
        urls = self.get_all_offers_urls()
        asyncio.run(self.collect_osint_data(urls))
        self.send_data_to_server(
            host,
            port,
            client_socket,
            [offer_details.convert_to_json() for offer_details in self.collected_osint_data],
        )
