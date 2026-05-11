FROM python:3.11-slim

WORKDIR /app

COPY setup.py .
COPY main.py .
COPY README.md .
COPY src/ ./src/
COPY model/ ./model/
COPY scripts/ ./scripts/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .[rl]

VOLUME ["/app/model/pbt_checkpoints", "/app/runs"]

ENV ITERATIONS=5
CMD ["sh", "-c", "python main.py pbt-train --iterations ${ITERATIONS}"]
