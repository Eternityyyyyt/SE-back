FROM python:3.11

ENV DEPLOY 1

WORKDIR /app

COPY requirements.txt .

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
RUN pip install "uvicorn[standard]"

# COPY . .

# EXPOSE 80

# CMD ["./start.sh"]

WORKDIR /app
COPY . /app

RUN python manage.py makemigrations user chat
RUN python manage.py migrate

CMD ["uvicorn","SE-back.asgi:application", "--host","0.0.0.0","--port","80", "--workers","1"]