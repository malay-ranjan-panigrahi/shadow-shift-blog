FROM nginx:alpine

# We use an argument to specify whether to build v1 or v2
ARG VERSION=v1

# Remove default Nginx page
RUN rm -rf /usr/share/nginx/html/*

# Copy our custom HTML into the container
COPY ${VERSION}/index.html /usr/share/nginx/html/index.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
