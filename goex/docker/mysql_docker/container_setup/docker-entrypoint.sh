#!/bin/bash
# docker-entrypoint.sh

# Start MySQL service
service mysql start

# Wait for MySQL to start up
sleep 10

exec "$@"
