FROM public.ecr.aws/docker/library/python@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

WORKDIR /app

RUN pip install --no-cache-dir \
    pytest==8.3.4 \
    pytest-json-ctrf==0.5.3

RUN mkdir -p /app/data /data /app /usr/local/libexec/dynamo

COPY generate_data.py /app/generate_data.py
COPY augment_data.py /tmp/augment_data.py
RUN install -m 0644 /tmp/augment_data.py /usr/local/libexec/dynamo/augment_data.py \
    && python3 /app/generate_data.py \
    && python3 /usr/local/libexec/dynamo/augment_data.py \
    && rm -f /tmp/augment_data.py
