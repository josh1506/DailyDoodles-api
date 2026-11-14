FROM postgres:15

COPY ./compose/production/postgres/maintenance /usr/local/bin/maintenance
# Strip CRLF in case the build context came from a Windows checkout (same as the django image).
RUN find /usr/local/bin/maintenance -type f -exec sed -i "s/\r$//" {} +
RUN chmod +x /usr/local/bin/maintenance/*
RUN mv /usr/local/bin/maintenance/* /usr/local/bin \
    && rmdir /usr/local/bin/maintenance
