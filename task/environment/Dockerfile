FROM public.ecr.aws/docker/library/python@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

WORKDIR /app

RUN pip install --no-cache-dir \
    pytest==8.3.4 \
    pytest-json-ctrf==0.5.3

RUN mkdir -p /app/data /data /app

COPY generate_data.py /tmp/generate_data.py
RUN python3 /tmp/generate_data.py && rm /tmp/generate_data.py
