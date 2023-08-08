"""
Consumer Script for RealTimeDataPipeline

This script is responsible for consuming messages from a Kafka topic and storing the relevant data into a PostgreSQL database.

Key Features:
    - Kafka Consumer: Connects to a Kafka broker and subscribes to a specific topic.
    - PostgreSQL Integration: Inserts the consumed data into PostgreSQL tables.
    - Data Parsing: Parses the incoming Kafka messages and extracts relevant data.

Environment Variables:
    - POSTGRES_DB: Name of the PostgreSQL database.
    - POSTGRES_USER: Username for the PostgreSQL database.
    - POSTGRES_PASSWORD: Password for the PostgreSQL database.

Dependencies:
    - psycopg2: PostgreSQL database adapter for Python.
    - confluent_kafka: Confluent's Kafka Python client.

Author: Boyd Werkman
Date: 8-8-2023
"""

import psycopg2
from confluent_kafka import Consumer, KafkaError
import json
import os

# Kafka Configuration
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

# Database Configuration
DB_HOST = "postgres"
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Establishing a connection to the PostgreSQL database
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
)
cur = conn.cursor()

# Create tables if they don't exist
# Train table stores general information about train events
# Coach table stores detailed information about individual coaches and their load values
cur.execute("""
CREATE TABLE IF NOT EXISTS Train (
    fid VARCHAR(255) PRIMARY KEY,
    rid VARCHAR(255),
    tpl VARCHAR(255),
    wta TIME,
    wtd TIME,
    pta TIME,
    ptd TIME,
    timestamp TIMESTAMP
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS Coach (
    id SERIAL PRIMARY KEY,
    fid VARCHAR(255),
    coach_number VARCHAR(50),
    load_value INT,
    FOREIGN KEY (fid) REFERENCES Train(fid),
    timestamp TIMESTAMP
)
""")

conn.commit()

# Setting up the Kafka consumer
consumer = Consumer(consumer_conf)
consumer.subscribe([KAFKA_TOPIC])

# Continuous polling of messages from the Kafka topic
while True:
    message = consumer.poll(1.0)
    if message is None:
        continue
    if message.error():
        print(f"Error while consuming message: {message.error()}")
        continue

    # Parsing the received message and extracting relevant data
    data = json.loads(message.value())
    coaches = data.pop("coaches")

    # Inserting data into the Train table
    insert_train_query = """
    INSERT INTO Train (fid, rid, tpl, wta, wtd, pta, ptd, timestamp)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (fid) DO UPDATE
    SET rid = EXCLUDED.rid, tpl = EXCLUDED.tpl, wta = EXCLUDED.wta, wtd = EXCLUDED.wtd, pta = EXCLUDED.pta, ptd = EXCLUDED.ptd, timestamp = EXCLUDED.timestamp;
    """
    cur.execute(insert_train_query, (data["fid"], data["rid"], data["tpl"], data["wta"], data["wtd"], data["pta"], data["ptd"], data["timestamp"]))
    conn.commit()

    # Inserting data into the Coach table
    for coach in coaches:
        insert_coach_query = """
        INSERT INTO Coach (fid, coach_number, load_value, timestamp)
        VALUES (%s, %s, %s, %s)
        """
        cur.execute(insert_coach_query, (data["fid"], coach["coach_number"], coach["load_value"], data["timestamp"]))
    conn.commit()

    print(f"Received message (key={message.key()}): {message.value()}")
