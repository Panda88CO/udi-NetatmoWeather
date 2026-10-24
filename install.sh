#!/usr/bin/env bash
if command -v pip3 >/dev/null 2>&1; then
    pip3 install --upgrade pip
    pip3 install -r requirements.txt --user
elif command -v pip >/dev/null 2>&1; then
    pip install --upgrade pip
    pip install -r requirements.txt --user
else
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt --user
fi
