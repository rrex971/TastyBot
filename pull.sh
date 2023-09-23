#!/bin/sh
pkill -f main.py
git pull
python main.py
