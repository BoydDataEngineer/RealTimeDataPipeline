# RealTimeDataPipeline

This repository contains the code for a real-time data pipeline that leverages Kafka for message processing and PostgreSQL for data storage. The pipeline consists of a producer that fetches data from the National Rail's STOMP server and a consumer that processes and stores this data in a database.

## Project Structure

- `consumer/consumer.py`: This script connects to a Kafka topic, consumes messages, processes them, and stores the data in PostgreSQL tables.
- `producer/producer.py`: This script connects to the National Rail's STOMP server, receives and processes messages, and then sends them to a Kafka topic.
- `docker-compose.yaml`: Defines the Docker services, networks, and volumes required for the project.

## Setup and Running

1. **Clone the Repository**
    ```bash
    git clone https://github.com/BoydDataEngineer/RealTimeDataPipeline.git
    ```

2. **Navigate to the Project Directory**
    ```bash
    cd RealTimeDataPipeline
    ```

3. **Set Up Environment Variables**

    Create a `.env` file in the root directory of the project and populate it with the following:

    ```makefile
    POSTGRES_USER=...
    POSTGRES_PASSWORD=...
    POSTGRES_DB=...
    PGADMIN_DEFAULT_EMAIL=...
    PGADMIN_DEFAULT_PASSWORD=...
    USERNAME_API=...
    PASSWORD_API=...
    ```

    To obtain the `USERNAME_API` and `PASSWORD_API` values:
    - Create an account on National Rail's Open Data platform.
    - Once logged in, navigate to "My Feeds".
    - Scroll down to "Darwin Topic Information" to find the username and password.

4. **Start Docker Services**
    ```bash
    docker-compose up
    ```

5. **Create Kafka Topic**

    After the services are running, execute:

    ```bash
    docker-compose exec kafka kafka-topics --create --topic train_loading --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1
    ```

6. **Access and Set Up PGAdmin**

    - Open a web browser and go to http://localhost:5050.
    - Log in using the `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` values you set in the .env file.
    - Right-click on "Servers" in the left panel and select "Create" > "Server".
    - Name the server (e.g., "RealTimeDataPipelineDB").
    - Under the "Connection" tab, set:
      - Host: postgres
      - Port: 5432
      - Maintenance database: Your `POSTGRES_DB` value
      - Username: Your `POSTGRES_USER` value
      - Password: Your `POSTGRES_PASSWORD` value
    - Click "Save".

## Data Description

### Train Table

- `fid`: Unique identifier for the train.
- `rid`: Train route identifier.
- `tpl`: Train platform.
- `wta`: Scheduled arrival time.
- `wtd`: Scheduled departure time.
- `pta`: Predicted arrival time.
- `ptd`: Predicted departure time.
- `timestamp`: Timestamp of the data entry.

### Coach Table

- `id`: Unique identifier for the coach entry.
- `fid`: Foreign key referencing the `fid` in the Train table.
- `coach_number`: Identifier for the coach.
- `load_value`: Load value indicating the occupancy or capacity on a scale from 0 (lowest loading) to 100 (highest loading).
- `timestamp`: Timestamp of the data entry.

## Querying the Data

1. **Access PGAdmin**

    Open a web browser and go to http://localhost:5050. Log in using the `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` values you set in the .env file.

2. **Navigate to Your Database**

    In PGAdmin, expand the Servers tree in the left panel. Navigate to Servers > RealTimeDataPipelineDB > Databases > Your `POSTGRES_DB` value.

3. **Open the Query Tool**

    Right-click on your database (<Your `POSTGRES_DB` value>) and select Query Tool from the context menu. This will open a new tab where you can write and execute SQL queries.

4. **Example Queries**

    ```sql
    -- To view all data in the 'Train' table:
    SELECT * FROM Train;

    -- To view all data in the 'Coach' table:
    SELECT * FROM Coach;

    -- To join data from both 'Train' and 'Coach' tables based on the `fid`:
    SELECT t.*, c.coach_number, c.load_value
    FROM Train t
    JOIN Coach c ON t.fid = c.fid;
    ```

## Dependencies

This project uses several libraries, including `confluent_kafka` for Kafka communication, `psycopg2` for PostgreSQL interactions, and `stomp` for STOMP server connections.
