FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV FLASK_ENV=development

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--reload", "run:app"]
