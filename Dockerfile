FROM python:3.11-alpine

WORKDIR /src

COPY pyproject.toml poetry.lock .python-version requirements.yaml docker_prepare.sh /src/

ARG CI_JOB_TOKEN
ARG GITLAB_PAT
ENV PATH /root/.local/bin:$PATH
ENV VERIFY_CHECKSUM false

# hadolint ignore=DL4006,DL3018,SC1091
RUN set -ex; \
    . /src/docker_prepare.sh; \
    apk add --update --no-cache \
        git \
        openssh-client-default \
        bash \
        shellcheck \
        gcc \
        libc-dev \
        libffi-dev \
        curl \
        ; \
    pip --no-cache-dir install poetry==1.7.1; \
    poetry config repositories.irp_openapi_client https://git.servers.im/irp/infra/irp_openapi_client.git; \
    poetry config http-basic.irp_openapi_client "${GITLAB_USER}" "${GITLAB_TOKEN}"; \
    poetry config virtualenvs.create false; \
    poetry  install --no-cache  -n --no-root; \
    ansible --version; \
    ansible-galaxy collection install -r requirements_docker.yaml; \
    curl -L https://dl.k8s.io/release/v1.27.5/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl; \
    chmod +x /usr/local/bin/kubectl; \
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash; \
    helm plugin install https://github.com/databus23/helm-diff; \
    apk del --purge gcc libc-dev libffi-dev
