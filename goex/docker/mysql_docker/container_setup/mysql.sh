#!/bin/bash

# Install MySQL server
apt-get update
apt install -y mysql-server

# Start MySQL service
usermod -d /var/lib/mysql/ mysql
service mysql start

# Configure MySQL
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '';"
mysql -e "FLUSH PRIVILEGES"
