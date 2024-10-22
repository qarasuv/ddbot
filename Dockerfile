FROM python:3.11

WORKDIR /app

COPY . .

RUN source setenv.sh

RUN pip install -r requirements.txt

CMD [ "python", "bot.py" ]