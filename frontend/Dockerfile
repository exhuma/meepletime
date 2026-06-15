FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
# Build-time metadata. APP_VERSION (from the release git tag) is read
# by vite.config.ts; VITE_GITHUB_REPO_URL is picked up by Vite as a
# VITE_* var and drives the footer's source-code link. Both must be
# declared here in the frontend build stage, before `npm run build`.
ARG APP_VERSION
ARG VITE_GITHUB_REPO_URL
ENV VITE_APP_VERSION=$APP_VERSION
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
