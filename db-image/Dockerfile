FROM postgres:16

# Build and install pgvector from source for reproducible install
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      postgresql-server-dev-16 \
      git \
      ca-certificates \
      wget \
    && rm -rf /var/lib/apt/lists/* && \
    git clone --depth 1 https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && \
    make && make install && \
    rm -rf /tmp/pgvector
