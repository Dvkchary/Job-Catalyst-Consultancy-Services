# ==============================================================================
# JobCatalyst AI - Ingress Reverse Proxy / Load Balancer Dockerfile (Nginx)
# ==============================================================================

FROM nginx:1.25-alpine

# Set up configuration directories
WORKDIR /etc/nginx

# Remove default configurations
RUN rm -rf /etc/nginx/conf.d/* /etc/nginx/nginx.conf

# Copy custom configurations
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

# Create SSL directories for HTTPS certificates (for staging/production)
RUN mkdir -p /etc/nginx/ssl

# Secure the pid file and folder permissions to run as non-root (nginx user)
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /var/log/nginx /etc/nginx

USER nginx

# Expose HTTP (80) and HTTPS (443)
EXPOSE 80
EXPOSE 443

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD nginx -t || exit 1

CMD ["nginx", "-g", "daemon off;"]
