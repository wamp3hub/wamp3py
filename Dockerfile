RUN https://github.com/wamp3hub/wamp3router/releases/latest/download/wamp3router-linux-amd64.out

RUN python3.12 -m pytest
