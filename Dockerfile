FROM python:3.9-slim

# Install Tesseract OCR and dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Flask default is 5000)
EXPOSE 5000

# Start the app
CMD ["python", "app.py"]
