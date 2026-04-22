FROM ubuntu:26.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && \
	apt-get install --no-install-recommends -y \
	ca-certificates \
	python-is-python3 \
	python3 \
	&& rm -rf /var/lib/apt/lists/*

COPY extensions.lock.json /tmp/extensions.lock.json
COPY scripts/install_extensions.py /opt/install_extensions.py

RUN python /opt/install_extensions.py \
	/tmp/extensions.lock.json \
	/run/challenge/share/code/extensions

FROM ubuntu:26.04 AS runtime

LABEL org.opencontainers.image.title="fluffys-vscode-extensions"
LABEL org.opencontainers.image.description="Visual Studio Code extensions for pwn.college"

COPY --from=builder /run/challenge/share/code/extensions /run/challenge/share/code/extensions

CMD ["bash", "-lc", "find /run/challenge/share/code/extensions -maxdepth 1 -mindepth 1 -print | sort"]
