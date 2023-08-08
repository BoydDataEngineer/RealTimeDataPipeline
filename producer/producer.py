import stomp
import gzip
import logging
import xml.etree.ElementTree as ET
import json
from confluent_kafka import Producer
import time
import os

logging.basicConfig(
    filename='stream=sys.stdout',
    format='%(asctime)s %(levelname)s\t%(message)s',
    level=logging.INFO
)

class MyListener(stomp.ConnectionListener):
    def on_error(self, frame):
        logging.error('Received an error "%s"' % frame.body)

    def on_disconnected(self):
        logging.error('Disconnected from the STOMP server. Attempting to reconnect...')
        reconnect()

    def on_message(self, frame):
        compressed_data = frame.body
        decompressed_data = gzip.decompress(compressed_data)
        logging.info(f"Received message: {decompressed_data}")
  
        root = ET.fromstring(decompressed_data)
        if root is None:
            logging.error("Failed to parse XML.")
            return

        # Extract the timestamp attribute from the Pport tag
        timestamp = root.get("ts")

        # Extract formationLoading attributes and coach loading values
        namespaces = {
            "default": "http://www.thalesgroup.com/rtti/PushPort/v16",
            "ns6": "http://www.thalesgroup.com/rtti/PushPort/Formations/v1"
        }

        formation_loading = root.find("default:uR/default:formationLoading", namespaces=namespaces)
        if formation_loading is not None:
            data_to_send = {
                "timestamp": timestamp,
                "fid": formation_loading.get("fid"),
                "rid": formation_loading.get("rid"),
                "tpl": formation_loading.get("tpl"),
                "wta": formation_loading.get("wta"),
                "wtd": formation_loading.get("wtd"),
                "pta": formation_loading.get("pta"),
                "ptd": formation_loading.get("ptd"),
                "coaches": []
            }

            for loading in formation_loading.findall("ns6:loading", namespaces=namespaces):
                coach_info = {
                    "coach_number": loading.get("coachNumber"),
                    "load_value": loading.text
                }
                data_to_send["coaches"].append(coach_info)

            # Convert the data to a JSON string
            json_data = json.dumps(data_to_send)

            # Produce to Kafka
            producer.produce(KAFKA_TOPIC, key=timestamp, value=json_data)
            producer.flush()

            print(f"Received message at: {timestamp}")


def reconnect():
    while True:
        try:
            conn.connect(USERNAME, PASSWORD, wait=True)
            conn.subscribe(destination=TOPIC, id=1, ack='auto', headers={'selector': "MessageType = 'LO'"})
            logging.info('Successfully reconnected to the STOMP server.')
            break  # Exit the loop once reconnected
        except Exception as e:
            logging.error(f"Failed to reconnect: {e}")
            time.sleep(5)  # Wait for 5 seconds before trying to reconnect


HOSTNAME = "darwin-dist-44ae45.nationalrail.co.uk"
HOSTPORT = 61613
USERNAME = os.getenv("USERNAME_API")
PASSWORD = os.getenv("PASSWORD_API")
TOPIC = "/topic/darwin.pushport-v16"

KAFKA_BROKER = 'kafka:9092'
KAFKA_TOPIC = 'train_loading'

producer_conf = {
    'bootstrap.servers': KAFKA_BROKER,
}

producer = Producer(producer_conf)

MAX_RETRIES = 5
RETRY_DELAY = 5  # in seconds

conn = stomp.Connection([(HOSTNAME, HOSTPORT)], auto_decode=False)
conn.set_listener('', MyListener())

# Retry mechanism for the initial connection
for i in range(MAX_RETRIES):
    try:
        conn.connect(USERNAME, PASSWORD, wait=True)
        break
    except stomp.exception.ConnectFailedException:
        if i < MAX_RETRIES - 1:
            print(f"Connection failed. Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
        else:
            print("Max retries reached. Exiting...")
            raise

# Once connected, proceed to subscribe
conn.subscribe(destination=TOPIC, id=1, ack='auto', headers={'selector': "MessageType = 'LO'"})

# Keep the script running
while True:
    time.sleep(10) 