FROM python:3.12.1-bookworm

RUN apt-get update -y

WORKDIR /wamp3py

RUN wget https://github.com/wamp3hub/wamp3router/releases/latest/download/wamp3router-linux-amd64.out

RUN chmod +x wamp3router-linux-amd64.out

RUN ./wamp3router-linux-amd64.out run &

RUN COPY . .

CMD python3.12 -m pytest
