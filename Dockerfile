# Use the official Python image with a specific version (e.g., 3.9)
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /restapi
# Install dependencies required for mysqlclient
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*
# Copy requirements and install them
COPY requirements.txt /restapi/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files into the container
COPY . /restapi/

# Expose the port Django will run on
EXPOSE 8000

# Run the Django development server (for production, use a WSGI server like Gunicorn)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

