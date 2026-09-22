# Use an official lightweight Python image
FROM python:3.12-slim

# Prevent Python from creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Display Python output immediately
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the dependency file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the complete backend application
COPY . .

# Create the persistent database directory
RUN mkdir -p /app/data

# Create a symbolic link for the SQLite database
RUN ln -s /app/data/resqcloud.db /app/resqcloud.db

# Expose the Flask application port
EXPOSE 5000

# Start the Flask application
CMD ["python", "app.py"]