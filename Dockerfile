FROM python:3.9.3

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /scraper

COPY ./scraper/ /scraper/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN apt update -y && apt install vim -y && apt install libpq-dev -y && apt install firefox-esr -y && apt install cron -y
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz
RUN tar -xzvf geckodriver-v0.33.0-linux64.tar.gz
RUN mv geckodriver /usr/local/bin
RUN crontab -l | { cat; echo "0 12 * * * python3 /scraper/scraper.py"; } | crontab -

CMD [ "python", "scraper.py" ]
