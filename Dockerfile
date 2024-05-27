FROM python:3.11-slim

# Set environment variables
ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=0 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set the working directory to /app
WORKDIR /app

# Copy files to the image
COPY ./ /app

# Install the required packages
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expose application port
EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
