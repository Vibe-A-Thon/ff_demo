FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package.json frontend/yarn.lock* ./
RUN corepack enable && if [ -f yarn.lock ]; then yarn install --frozen-lockfile; else yarn install; fi

COPY frontend/ ./

ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

RUN yarn build

FROM nginx:1.25-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
