FROM alpine

RUN apk --no-cache add tzdata tini

ENTRYPOINT ["tini", "--"]
CMD ["crond", "-f"]