# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Run the wait-for-it script to wait for the broker to be ready
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run the producer script when the container launches
CMD ["python", "producer.py"]
