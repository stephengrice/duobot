FROM "selenium/node-firefox"

RUN sudo apt update \
    && sudo apt install -y vim python3 python3-pip \
    && sudo rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip3 install --user -r /app/requirements.txt
COPY . /app
RUN sudo chown seluser:seluser /app -R