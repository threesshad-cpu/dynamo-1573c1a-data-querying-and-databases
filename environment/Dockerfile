FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

WORKDIR /app

RUN pip install --no-cache-dir \
    pytest==8.3.4 \
    pytest-json-ctrf==0.1.0 \
    rdflib==7.1.1 \
    networkx==3.4.2 \
    numpy==2.2.1

RUN mkdir -p /app/data /logs/verifier

COPY environment/generate_data.py /tmp/generate_data.py
RUN python3 /tmp/generate_data.py && rm /tmp/generate_data.py
