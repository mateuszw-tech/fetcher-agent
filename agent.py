from settings import SprzedajemySettings
from fetcher import SprzedajemyFetcher, AdvertisementInfo
from queue import Queue
import asyncio
import json
from queue import Empty


class Agent:
    def __init__(self, *fetchers):
        self.fetchers = fetchers
        self.sprzedajemy_fetcher = SprzedajemyFetcher("Malbork")
        self.host_address = "127.0.0.1"
        self.port = 55555
        self.collected_osint_data: Queue = Queue()

    async def receive_instructions_from_server(self, reader: asyncio.StreamReader) -> None:
        while True:
            instructions = await reader.read(1024)
            await self.instructions_handler(instructions.decode())

    async def instructions_handler(self, instructions: str) -> None:
        if instructions.startswith("fetch"):
            await self.sprzedajemy_fetcher.start_fetching_data(self.collected_osint_data)
        elif instructions.startswith("stop"):
            self.sprzedajemy_fetcher.fetching_status = False

    async def connect(self) -> None:
        reader, writer = await asyncio.open_connection(self.host_address, self.port)

        receive_instructions_task = asyncio.create_task(self.receive_instructions_from_server(reader))
        send_data_task = asyncio.create_task(self.send_data_to_server(writer, self.collected_osint_data))
        await receive_instructions_task
        await send_data_task

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

    def run(self):
        asyncio.run(self.connect())
