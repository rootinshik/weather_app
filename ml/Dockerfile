FROM python:3.12-slim

WORKDIR /app/ml

ENV PYTHONPATH=/app

COPY requirements.txt /app/ml/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/ml/

CMD ["python", "train.py"]
