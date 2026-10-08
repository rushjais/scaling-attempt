# Pilot sandbox for the Pelican migration task: Linux (path semantics pinned),
# Python 3.11, Pelican's runtime + test dependencies, locales for the
# custom_locale golden site, git, and Claude Code. Pelican itself is NOT in the
# image: each attempt mounts a fresh checkout at /work/repo (on PYTHONPATH).
FROM python:3.11-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends git nodejs npm ca-certificates locales \
 && sed -i 's/^# *\(en_US.UTF-8\|fr_FR.UTF-8\)/\1/' /etc/locale.gen && locale-gen \
 && rm -rf /var/lib/apt/lists/* \
 && npm install -g @anthropic-ai/claude-code

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

ENV HOME=/home/agent LANG=en_US.UTF-8 PYTHONPATH=/work/repo TZ=UTC
RUN mkdir -p /home/agent && chmod 777 /home/agent \
 && git config --system user.name dev && git config --system user.email dev@example.com \
 && git config --system --add safe.directory '*'
WORKDIR /work/repo
