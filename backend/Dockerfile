FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir
RUN pip install gunicorn

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi:application"]