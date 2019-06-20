#!/usr/bin/env bash

cd ~/PycharmProjects/html2rss/
source ./venv/bin/activate
python html2rss.py $@
deactivate
