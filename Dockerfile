# ==============================================================================
# JobCatalyst AI - Production Frontend Dockerfile
# ==============================================================================

# Stage 1: Build the static React application
FROM node:20-alpine AS builder

WORKDIR /app

# Enable layer caching for npm dependencies
COPY package*.json ./

RUN npm ci

# Copy configuration and source files
COPY tsconfig.json vite.config.ts index.html ./
COPY src/ ./src/
COPY assets/ ./assets/

# Inject environment variables during build time if necessary (Vite prefix)
# ARG VITE_API_URL
# ENV VITE_API_URL=$VITE_API_URL

# Build production optimized build (outputs to /app/dist)
RUN npm run build


# Stage 2: Serve compiled static files using a hardened Nginx alpine image
FROM nginx:1.25-alpine

# Set up directories and clean default configs
WORKDIR /usr/share/nginx/html
RUN rm -rf ./*

# Copy built files from Builder stage
COPY --from=builder /app/dist .

# Copy lightweight custom Nginx config for static serving on port 3000
COPY nginx.frontend.conf /etc/nginx/conf.d/default.conf

# Create a non-root system user and change permissions of Nginx write folders
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /var/log/nginx /usr/share/nginx/html

# Switch to the non-privileged user
USER nginx

# Expose the standard frontend port
EXPOSE 3000

# Health check to ensure frontend is serving requests
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
