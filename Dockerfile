# Use an official CUDA-enabled Python runtime as a parent image
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

# Set non-interactive installation to avoid timezone prompt
ENV DEBIAN_FRONTEND=noninteractive

# Install Python (if not included in the image)
RUN apt-get update && apt-get install -y python3-pip python3-dev && ln -s $(which python3) /usr/local/bin/python

# Continue with your application setup
WORKDIR /app

# Install FFmpeg and other dependencies
RUN apt-get update && apt-get install -y ffmpeg

# Copy and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000

CMD ["python", "main.py"]