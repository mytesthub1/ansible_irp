#!/bin/sh
set -e
if [ -n "${CI_JOB_TOKEN}" ]; then
  export GITLAB_USER=gitlab-ci-token
  export GITLAB_TOKEN="${CI_JOB_TOKEN}"

else
  if [ -n "${GITLAB_PAT}" ]; then
    export GITLAB_USER=__token__
    export GITLAB_TOKEN="${GITLAB_PAT}"
  else
    echo
    printf "\033[1;31m!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\033[0m\n"
    echo
    printf "\033[1mYou should specify Gitlab Personal access token via --build-arg GITLAB_PAT=your_token for local build\n"
    echo
    printf "\033[1;31m!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\033[0m\n"
    echo
    exit 1
  fi
fi

# Change git url scheme from ssh to https with gitlab token auth
sed "s/ssh:\/\/git@/https:\/\/${GITLAB_USER}:${GITLAB_TOKEN}@/g" requirements.yaml > requirements_docker.yaml
