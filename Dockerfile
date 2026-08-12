FROM python:3.12-slim
LABEL authors="Vadym Iskryzhytskyi"

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python db.py -a
RUN useradd -m app && chown -R app:app /app

USER app

EXPOSE 5000

ENTRYPOINT ["python", "app.py"]