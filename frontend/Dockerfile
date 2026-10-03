FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN --mount=type=secret,id=gandalf_build_ca,required=false \
    if [ -f /run/secrets/gandalf_build_ca ]; then \
        NODE_EXTRA_CA_CERTS=/run/secrets/gandalf_build_ca npm ci; \
    else \
        npm ci; \
    fi
COPY frontend/ ./
ENV VITE_API_BASE_URL=/api/v1
RUN npm run build

FROM nginx:stable-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
