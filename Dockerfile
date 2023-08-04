# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install the required dependencies including Gunicorn
RUN pip install --trusted-host pypi.python.org Flask Pillow gunicorn

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run Gunicorn with 4 worker processes and bind it to 0.0.0.0:8000
CMD ["gunicorn", "-w", "4", "thingy:app", "--bind", "0.0.0.0:8000"]
