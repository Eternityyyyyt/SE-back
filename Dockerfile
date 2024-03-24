FROM python:3.11

ENV DEPLOY 1

WORKDIR /app

COPY requirements.txt .

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

COPY . .

EXPOSE 80

COPY start.sh .

CMD ["sh ./start.sh"]