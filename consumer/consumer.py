import psycopg2
from confluent_kafka import Consumer, KafkaError
import json
import os

# Kafka Config
KAFKA_BROKER = 'kafka:9092'
KAFKA_TOPIC = 'train_loading'
GROUP_ID = 'my_consumer_group'

consumer_conf = {
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': GROUP_ID,
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
    'default.topic.config': {'auto.offset.reset': 'smallest'}
}

# Database Config
DB_HOST = "postgres"
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
)
cur = conn.cursor()

# Create tables if they don't exist
cur.execute("""
CREATE TABLE IF NOT EXISTS train_data (
    id serial PRIMARY KEY,
    key TEXT,
    timestamp TIMESTAMP,
    fid TEXT,
    rid TEXT,
    tpl TEXT,
    wta TIME,
    wtd TIME,
    pta TIME,
    ptd TIME
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS coaches_data (
    id serial PRIMARY KEY,
    train_data_id integer references train_data(id),
    timestamp TIMESTAMP,  -- added timestamp here
    coach_number TEXT,
    load_value INTEGER
)
""")

conn.commit()

consumer = Consumer(consumer_conf)
consumer.subscribe([KAFKA_TOPIC])

while True:
    message = consumer.poll(1.0)
    if message is None:
        continue
    if message.error():
        print(f"Error while consuming message: {message.error()}")
        continue

    data = json.loads(message.value())
    coaches = data.pop("coaches")
    message_timestamp = data["timestamp"]  # Extracted the timestamp to be used for coaches

    # Insert main data into train_data table
    insert_train_query = """
    INSERT INTO train_data (key, timestamp, fid, rid, tpl, wta, wtd, pta, ptd)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    """
    cur.execute(insert_train_query, (message.key(), data["timestamp"], data["fid"], data["rid"], data["tpl"], data["wta"], data["wtd"], data["pta"], data["ptd"]))
    train_data_id = cur.fetchone()[0]
    conn.commit()

    # Insert coaches data into coaches_data table
    for coach in coaches:
        insert_coach_query = """
        INSERT INTO coaches_data (train_data_id, timestamp, coach_number, load_value)  -- Added timestamp column here
        VALUES (%s, %s, %s, %s)
        """
        cur.execute(insert_coach_query, (train_data_id, message_timestamp, coach["coach_number"], coach["load_value"]))  # Added message_timestamp here
    conn.commit()

    print(f"Received message (key={message.key()}): {message.value()}")
