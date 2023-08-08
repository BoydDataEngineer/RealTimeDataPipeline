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

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
)
cur = conn.cursor()

# Create tables
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
    FOREIGN KEY (fid) REFERENCES Train(fid)
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

    # Insert into Train table
    insert_train_query = """
    INSERT INTO Train (fid, rid, tpl, wta, wtd, pta, ptd, timestamp)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (fid) DO UPDATE
    SET rid = EXCLUDED.rid, tpl = EXCLUDED.tpl, wta = EXCLUDED.wta, wtd = EXCLUDED.wtd, pta = EXCLUDED.pta, ptd = EXCLUDED.ptd, timestamp = EXCLUDED.timestamp;
    """
    cur.execute(insert_train_query, (data["fid"], data["rid"], data["tpl"], data["wta"], data["wtd"], data["pta"], data["ptd"], data["timestamp"]))
    conn.commit()

    # Insert into Coach table
    for coach in coaches:
        insert_coach_query = """
        INSERT INTO Coach (fid, coach_number, load_value)
        VALUES (%s, %s, %s)
        """
        cur.execute(insert_coach_query, (data["fid"], coach["coach_number"], coach["load_value"]))
    conn.commit()

    print(f"Received message (key={message.key()}): {message.value()}")
