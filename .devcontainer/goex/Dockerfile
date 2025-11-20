FROM mcr.microsoft.com/devcontainers/python:1-3.10

RUN apt-get update && apt-get install -y \
    mkcert \
    sqlite3

RUN curl -sfL https://direnv.net/install.sh | bash && \
    echo 'eval "$(direnv hook bash)"' >> /etc/bash.bashrc
