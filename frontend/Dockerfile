# 1) Compila o React com o Vite
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# 2) Serve os arquivos com o nginx (só para rodar local com docker compose;
#    na AWS os arquivos vão para o S3 + CloudFront)
FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
