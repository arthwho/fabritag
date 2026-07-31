FROM node:22-alpine AS build

WORKDIR /app

RUN corepack enable \
    && corepack prepare pnpm@10.28.0 --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
RUN pnpm install --frozen-lockfile

COPY . .

RUN pnpm run build


FROM node:22-alpine AS runtime

ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=3000

WORKDIR /app

COPY --from=build --chown=node:node /app/build ./build

USER node

EXPOSE 3000

CMD ["node", "build"]
