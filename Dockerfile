FROM python:3.11-slim

WORKDIR /app

COPY setup.py README.md ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .[rl]

COPY main.py .
COPY src/ ./src/
COPY model/ ./model/
COPY scripts/ ./scripts/

ENV PYTHONUNBUFFERED=1
ENV ITERATIONS=5
ENV NUM_WORKERS=4
CMD ["sh", "-c", "NUM_W=${NUM_WORKERS:-0}; [ \"$NUM_W\" = \"0\" ] && NUM_W=$(nproc); python main.py pbt-train --iterations ${ITERATIONS} --num-workers ${NUM_W}"]
