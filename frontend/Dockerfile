# NOTE: Dockerfile ini untuk `docker compose` lokal saja. Deploy production
# frontend langsung ke Vercel dari source (lihat frontend/vercel.json) —
# Vercel tidak memakai file ini.

FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

FROM nginx:alpine AS serve
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
