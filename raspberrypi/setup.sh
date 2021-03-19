#! /bin/bash

# download ca certificate
wget https://www.amazontrust.com/repository/AmazonRootCA1.pem -O certs/ca.pem

# install packages
sudo apt-get install -y nodejs npm

npm install aws-iot-device-sdk
