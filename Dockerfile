# Dockerfile

# --- Stage 1: Base Image ---
# Use an official Python image as a parent image.
# Using a specific version ensures consistency.
FROM python:3.11-slim-bookworm

# --- Stage 2: Setup Environment ---
# Set the working directory inside the container. All subsequent commands
# will run from this directory.
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --- Stage 3: Install Dependencies ---
# Copy only the requirements file first to leverage Docker's layer caching.
# This layer will only be rebuilt if requirements.txt changes.
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 4: Copy Application Code ---
# Copy the rest of your application's source code into the container.
# We copy the entire project context.
COPY . .

# --- Stage 5: Define the Runtime Command ---
# The command that will be run when the container starts.
# We point it to your main_listener.py script.
CMD ["python", "src/main.py"]
