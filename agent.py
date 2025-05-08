from queue import Queue
import re
import asyncio
from queue import Empty
from settings import Settings


class Agent:
    def __init__(self, fetchers: list):
        self.fetchers = fetchers
        self.host_address = "127.0.0.1"
        self.port = 55555
        self.collected_osint_data: Queue = Queue()
        self.settings: Settings = Settings()
        self.background_tasks = {}

    async def receive_instructions_from_server(self, reader: asyncio.StreamReader) -> None:
        while True:
            instructions = await reader.read(1024)
            await self.instructions_handler(instructions.decode())

    async def instructions_handler(self, instructions: str) -> None:
        if re.match(r"fetch", instructions):
            for fetcher in self.fetchers:
                if Settings.get_active_status(fetcher.fetcher_type):
                    fetcher.cities = Settings.get_cities_from_settings(fetcher.fetcher_type)
                    task = asyncio.create_task(fetcher.start_fetching(
                        self.collected_osint_data,
                        Settings.get_iteration_time_from_settings_file(fetcher.fetcher_type)
                    ))
                    self.background_tasks[fetcher.fetcher_type] = task
        elif re.match(r"stop", instructions):
            for fetcher in self.fetchers:
                if fetcher.fetcher_type in self.background_tasks:
                    self.background_tasks[fetcher.fetcher_type].cancel()
                    del self.background_tasks[fetcher.fetcher_type]
        elif re.match(r"^\{.*}$", instructions):
            Settings.save_settings(instructions)

    async def connect(self) -> None:
        api_key = '100XF40'
        reader, writer = await asyncio.open_connection(self.host_address, self.port)

        writer.write(f"{api_key}".encode())
        await writer.drain()

        response = await reader.read(1024)
        response_message = response.decode('utf-8').strip()

        if "Invalid API key" in response_message:
            print("Server rejected connection: Invalid API key.")
            writer.close()
            await writer.wait_closed()
            return

        print("Connected to the server successfully!")

        receive_instructions_task = asyncio.create_task(self.receive_instructions_from_server(reader))
        send_data_task = asyncio.create_task(self.send_data_to_server(writer, self.collected_osint_data))

        await receive_instructions_task
        await send_data_task

    @staticmethod
    async def send_data_to_server(writer: asyncio.StreamWriter, data_queue: Queue) -> None:
        while True:
            try:
                data = data_queue.get(block=True, timeout=1)
                json_data = (data.return_as_json() + "\r\n")

                writer.write(json_data.encode(encoding="UTF-8", errors="ignore"))
                print(f"sent: {json_data.encode(encoding="utf-8", errors="ignore")}")
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
