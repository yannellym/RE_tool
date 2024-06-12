#!/bin/bash

# Install Python 3.8
wget https://www.python.org/ftp/python/3.8.12/Python-3.8.12.tgz
tar xzf Python-3.8.12.tgz
cd Python-3.8.12
./configure --enable-optimizations
make altinstall
cd ..
rm Python-3.8.12.tgz
rm -rf Python-3.8.12

# Activate Python 3.8
export PATH="/usr/local/bin:$PATH"

# Install pip
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.8 get-pip.py
rm get-pip.py

# Install dependencies
pip install -r requirements.txt
