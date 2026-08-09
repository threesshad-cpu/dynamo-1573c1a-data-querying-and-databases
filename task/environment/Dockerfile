FROM python:3.13-slim-bookworm

WORKDIR /app

RUN pip install --no-cache-dir \
    pytest==8.3.4 \
    pytest-json-ctrf==0.5.3

RUN mkdir -p /app/data /data /app

COPY generate_data.py /tmp/generate_data.py
RUN python3 /tmp/generate_data.py && rm /tmp/generate_data.py
