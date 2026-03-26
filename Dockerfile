FROM python:3.11-slim

WORKDIR /app

ARG PYPI_INDEX_URL=https://pypi.org/simple
ARG DEBIAN_MIRROR=deb.debian.org

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=hardlink \
    UV_PYTHON_DOWNLOADS=never \
    UV_DEFAULT_INDEX=${PYPI_INDEX_URL}

RUN if [ "$DEBIAN_MIRROR" != "deb.debian.org" ]; then \
      sed -i "s|deb.debian.org|${DEBIAN_MIRROR}|g" /etc/apt/sources.list.d/debian.sources; \
    fi

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv -i "${PYPI_INDEX_URL}"

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --no-install-project \
    && rm -rf /root/.cache/uv

COPY . .

RUN uv sync --frozen \
    && rm -rf /root/.cache/uv
RUN mkdir -p /app/data /app/logs /app/storage

EXPOSE 8888

CMD ["uv", "run", "--no-sync", "agent-py"]
