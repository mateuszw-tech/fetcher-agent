import concurrent
import json
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import List

from bs4 import BeautifulSoup
import asyncio
import aiohttp
from utils import SprzedajemyUtils, ScraperUtils
from queue import Queue
from queue import Empty


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


class SprzedajemyFetcher(Fetcher):  # NOQA

    def __init__(self, *cities: str):
        self.cities: tuple = cities
        self.collected_osint_data: Queue = Queue()
        self.fetching_status = True

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
        self.collected_osint_data.put(info)

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
            pass

    async def collect_osint_data(self, offer_list: list[str]) -> None:
        tasks = []
        for offer in offer_list:
            if self.fetching_status:
                task = asyncio.create_task(
                    ScraperUtils.fail_repeat_execution(self.load_advertisement_info_from_url, offer)
                )
                tasks.append(task)

        await asyncio.gather(*tasks)

    def change_cities(self, *cities: str) -> None:
        self.cities = cities

    @staticmethod
    async def send_data_to_server(writer: asyncio.StreamWriter, data_queue: Queue) -> None:
        while True:
            try:
                data = data_queue.get(block=True, timeout=1)
                json_data = json.dumps(data.convert_to_json() + "\r\n")

                writer.write(json_data.encode("ascii"))
                print(f"sent: {json_data.encode("ascii")}")
                await writer.drain()

            except Empty:
                print('Got nothing, waiting a while...')
                await asyncio.sleep(5)
            except ConnectionRefusedError:
                print("Connection refused. Closing writer.")
                writer.close()
                await writer.wait_closed()
                break

    async def receive_instructions_from_server(self, reader: asyncio.StreamReader) -> None:
        while True:
            instructions = await reader.read(1024)
            await self.instructions_handler(instructions.decode())

    async def instructions_handler(self, instructions: str):
        if instructions.startswith("fetch"):
            await self.start_fetching_data('127.0.0.1', 55555)
        elif instructions.startswith("stop"):
            self.fetching_status = False

    async def start_fetching_data(self, host: str, port: int) -> None:
        print("gathering data started...")
        urls = self.get_all_offers_urls()

        reader, writer = await asyncio.open_connection(host, port)
        send_data_task = asyncio.create_task(self.send_data_to_server(writer, self.collected_osint_data))

        await self.collect_osint_data(urls)

        await send_data_task

    async def connect(self, host: str, port: int) -> None:
        reader, writer = await asyncio.open_connection(host, port)

        receive_instructions_task = asyncio.create_task(self.receive_instructions_from_server(reader))
        await receive_instructions_task
