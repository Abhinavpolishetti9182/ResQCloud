# Use an official lightweight Python image
FROM python:3.12-slim

# Prevent Python from creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Display Python output immediately
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the dependency file first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the complete backend application
COPY . .

# Create a directory for the SQLite database
RUN mkdir -p /app/data

# Expose the Flask application port
EXPOSE 5000

# Start the Flask application
CMD ["python", "app.py"]