FROM python:alpine

RUN apk --no-cache add tzdata

ADD . /bot
WORKDIR /bot

RUN pip install -r requirements.txt

ENV TZ Asia/Tokyo

RUN cp /usr/share/zoneinfo/${TZ} /etc/localtime \
 && echo ${TZ} > /etc/timezone \
 && echo "30 11 * * * python /bot/main.py start" >> /etc/crontabs/root \
 && echo "30 21 * * * python /bot/main.py end" >> /etc/crontabs/root

CMD ["crond", "-f", "-d", "8", "-c", "/etc/crontabs"]