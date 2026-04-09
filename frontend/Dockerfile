FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN adduser -D -g '' appuser
RUN chown -R appuser:appuser /var/cache/nginx /var/run /var/log/nginx
USER appuser

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
