import time
import serial
import pubnub
import os
from dotenv import load_dotenv
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNOperationType, PNStatusCategory
from flask import Flask

app = Flask(__name__)

load_dotenv()

PUBNUB_CHANNEL = os.getenv("PUBNUB_CHANNEL")
MACHINE_ID = 1

pnconfig = PNConfiguration()
pnconfig.subscribe_key = os.getenv("PUBNUB_SUB_KEY")
pnconfig.publish_key = os.getenv("PUBNUB_PUB_KEY")
pnconfig.user_id = os.getenv("PUBNUB_UID")
pubnub = PubNub(pnconfig)

arduino = serial.Serial(port="COM4", baudrate=115_200, timeout=0.1)

current_second = 0


class MySubscribeCallback(SubscribeCallback):
    def __init__(self) -> None:
        super().__init__()
        self.listener_state = None
        self.current_seconds = 0
        self.review_id = None

    def message(self, pubnub, message):
        print(message.__dict__)

        if message.message == "start":
            self.listener_state = "STARTED"
            self.review_id = message.publisher
        if message.message == "stop":
            self.listener_state = "STOPPED"
            self.review_id = message.publisher

        if self.listener_state == "STARTED":
            byte = arduino.readline()
            decoded_bytes = byte.decode("utf-8")

            if not decoded_bytes == "":
                data_str = decoded_bytes.strip()
                data_tokens = data_str.split(", ")

                pub_list = []
                pub_list.append(self.review_id)
                pub_list.append(MACHINE_ID)
                pub_list += list(map(int, data_tokens))
                pub_list.append(self.current_seconds)

                self.current_seconds = self.current_seconds + 2
                pubnub.publish().channel(PUBNUB_CHANNEL).message(pub_list).pn_async(
                    publish_callback
                )
                time.sleep(2)


def publish_callback(_, status):
    if status.is_error():
        print("ERROR: failed publishing at {}s".format(current_second))


if __name__ == "__main__":
    pubnub.add_listener(MySubscribeCallback())
    pubnub.subscribe().channels(PUBNUB_CHANNEL).execute()
    app.run(port=5421)

    # if MySubscribeCallback().listener_state == "STARTED":
    #     break
