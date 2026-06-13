FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Runtime config: the entrypoint hook renders /config.js from
# MEEPLETIME_* env vars at container start (see the script below).
COPY config.template.js /etc/meepletime/config.template.js
COPY docker-entrypoint.d/40-meepletime-config.sh \
  /docker-entrypoint.d/40-meepletime-config.sh
RUN chmod +x /docker-entrypoint.d/40-meepletime-config.sh
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
