#!/bin/bash
mkdir -p ~/.ssh
ssh-keyscan -t rsa github.com >>~/.ssh/known_hosts
cd /app
if [[ ! -d /app/scouts ]]; then
    git clone https://github.com/bradjhays/scouts.git --branch main --single-branch
fi

cd scouts/$SERVICE
git pull
git log -n 1
export PIP_ROOT_USER_ACTION=ignore
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

pip install --upgrade pip --root-user-action=ignore
pip install -r requirements.txt --root-user-action=ignore >/dev/null
set -ex
python main.py $OPTS
