from settings import SprzedajemySettings
from fetcher import SprzedajemyFetcher
import asyncio


class Agent:
    def __init__(self, *fetchers):
        self.fetchers = fetchers
        self.host_address = "127.0.0.1"
        self.port = 55555

    def start_all_fetchers(self):
        for fetcher in self.fetchers:
            asyncio.run(fetcher.connect(
                self.host_address,
                self.port,
            ))

    def change_settings(self, settings_json: dict):
        pass
