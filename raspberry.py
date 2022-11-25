import serial
import pubnub
import os
from dotenv import load_dotenv
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

load_dotenv()

PUBNUB_CHANNEL = 'Moviology-Channel'
MACHINE_ID = 1

pnconfig = PNConfiguration()
pnconfig.subscribe_key = os.getenv('PUBNUB_SUBSCRIBE_KEY')
pnconfig.publish_key = os.getenv('PUBNUB_PUBLISH_KEY')
pnconfig.user_id = os.getenv('PUBNUB_USER_ID')
pubnub = PubNub(pnconfig)

arduino = serial.Serial(port='/dev/ACM0', baudrate=57600, timeout=.1)

current_second = 0


def publish_callback(_, status):
    if status.is_error():
        print("ERROR: failed publishing at {}s".format(current_second))


while True:
    byte = arduino.readline()
    decoded_bytes = byte.decode("utf-8")

    if not decoded_bytes == "":
        data_str = decoded_bytes.strip()
        data_tokens = data_str.split(', ')

        pub_list = list(map(int, data_tokens))
        pub_list.append(current_second)
        pub_list.append(MACHINE_ID)

        current_second = current_second + 2
        pubnub.publish().channel(PUBNUB_CHANNEL).message(pub_list).pn_async(publish_callback)
