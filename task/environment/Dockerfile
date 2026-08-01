FROM python:3.13-slim-bookworm

WORKDIR /app

RUN pip install --no-cache-dir \
    pytest==8.3.4 \
    pytest-json-ctrf==0.1.0 \
    rdflib==7.1.1 \
    networkx==3.4.2 \
    numpy==2.2.1

RUN mkdir -p /app/data /data /logs/verifier


COPY generate_data.py /tmp/generate_data.py
RUN python3 /tmp/generate_data.py && rm /tmp/generate_data.py
