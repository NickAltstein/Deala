# Pinned wawatch (tupe12334/wawatch) plus a thin inbound bridge.
# There is no published Docker image for this fork. FastAPI never talks to it
# over stdio; the bridge POSTs JSON to the backend webhook.
FROM node:22-bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/wawatch
ARG WAWATCH_COMMIT=21cc35ebc83827173bcea51a971b9bcd4c9362f8
RUN git init \
    && git remote add origin https://github.com/tupe12334/wawatch.git \
    && git fetch --depth 1 origin ${WAWATCH_COMMIT} \
    && git checkout --detach FETCH_HEAD \
    && rm -rf .git \
    && sed -i "s/createMcpExpressApp({ host: '127.0.0.1' })/createMcpExpressApp({ host: '0.0.0.0' })/" src/server.ts \
    && sed -i "s/app.listen(Number(args.port), '127.0.0.1'/app.listen(Number(args.port), '0.0.0.0'/" src/cli.ts \
    && npm ci \
    && npm run build

COPY bridge.mjs /opt/deala/bridge.mjs
COPY entrypoint.sh /opt/deala/entrypoint.sh
RUN chmod +x /opt/deala/entrypoint.sh

ENV WAWATCH_PORT=3001 \
    WAWATCH_DATA=/data
EXPOSE 3001
VOLUME ["/data"]
ENTRYPOINT ["/opt/deala/entrypoint.sh"]
