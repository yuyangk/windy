from joyzoursky/python-chromedriver:3.9

COPY requirements.txt /requirements.txt
 
RUN set -x \
   && apt-get update \
   && apt-get upgrade -y \
   && apt-get install -y \
       firefox-esr \
   && pip install --upgrade pip \
   && pip install -r /requirements.txt

RUN mkdir /app
 
WORKDIR /app
