# Bước 1: Build source code bằng Node
FROM node:18-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Bước 2: Dùng Nginx để chạy file đã build
FROM nginx:stable-alpine as production-stage
# Copy file build vào thư mục của Nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html
# Copy file eda.json và training_log.csv vào đúng chỗ để dashboard đọc được
COPY --from=build-stage /app/public /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]