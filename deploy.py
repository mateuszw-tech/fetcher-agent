import json
import time
import asyncio
from fetcher import SprzedajemyFetcher
import socket
import threading
from agent import Agent

agent = Agent()

info_list = []

HOST = "127.0.0.1"
PORT = 55555

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

fetchers = []


def fetch():
    fetcher = SprzedajemyFetcher("Malbork")
    # Agent.settings(fetcher, "Malbork", "Chełm")
    urls = fetcher.get_all_offers_urls()
    asyncio.run(fetcher.load_osint_data_async(urls))
    for data in fetcher.get_osint_data():
        info_list.append(data.convert_to_json())


def send_data():
    fetch()
    json_data = json.dumps(info_list)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.send(json_data.encode("utf-8"))
        print(f"Sent JSON data: {json_data}")
        s.close()


send_data()

time.sleep(60)

send_data()
