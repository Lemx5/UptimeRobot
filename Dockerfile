# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable (example for MongoDB, you can add others)
ENV DB_URI=mongodb://localhost:27017/

# Run bot.py when the container launches
CMD ["python", "bot.py"]
