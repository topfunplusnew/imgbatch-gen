FROM python:3.11-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_DEFAULT_INDEX=https://mirrors.aliyun.com/pypi/simple/

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv -i https://mirrors.aliyun.com/pypi/simple/

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --no-install-project

COPY . .

RUN uv sync --frozen
RUN mkdir -p /app/storage

EXPOSE 8888

CMD ["uv", "run", "--no-sync", "agent-py"]
