FROM python:3.11-slim

WORKDIR /app

COPY setup.py README.md ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .[rl]

COPY main.py .
COPY src/ ./src/
COPY model/ ./model/
COPY scripts/ ./scripts/

ENV ITERATIONS=5
CMD ["sh", "-c", "python main.py pbt-train --iterations ${ITERATIONS}"]
