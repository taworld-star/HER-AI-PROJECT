# Stage 1: builder – inject runtime config into JS
FROM node:20-alpine AS builder

WORKDIR /app
COPY . .

# The sed runs at build time so the static bundle is already correct.
RUN sed -i 's|http://localhost:5000/api|https://siklika-api.neoartd.my.id/api|g' app.js \
    && sed -i 's|http://localhost:5000/api|https://siklika-api.neoartd.my.id/api|g' dashboard.js \
    && sed -i 's|http://localhost:5000/api|https://siklika-api.neoartd.my.id/api|g' chatbot.js \
    && sed -i 's|http://localhost:5000/api|https://siklika-api.neoartd.my.id/api|g' riwayat.js \
    || true   # tolerate files that don't contain the pattern

# Stage 2: nginx serving static files 
FROM nginx:1.27-alpine AS runtime

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static assets from builder
COPY --from=builder /app /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]