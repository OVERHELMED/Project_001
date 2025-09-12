#!/bin/bash

# Force Python 3.10 installation
echo "Installing Python 3.10..."
curl -O https://www.python.org/ftp/python/3.10.12/Python-3.10.12.tgz
tar -xzf Python-3.10.12.tgz
cd Python-3.10.12
./configure --enable-optimizations
make -j 8
make altinstall
cd ..

# Use Python 3.10 to install requirements
echo "Installing requirements with Python 3.10..."
python3.10 -m pip install --upgrade pip
python3.10 -m pip install -r requirements-python310.txt

echo "Installation completed!"
