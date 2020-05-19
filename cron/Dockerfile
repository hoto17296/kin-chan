FROM alpine

RUN apk --no-cache add tzdata tini

ENV TZ "Asia/Tokyo"
ADD crontab /var/spool/cron/crontabs/root

ENTRYPOINT ["tini", "--"]
CMD ["crond", "-f"]
