FROM python:3.10-slim

# Install dependencies for PyAudio build
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    portaudio19-dev \
    libasound-dev \
    ffmpeg \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
