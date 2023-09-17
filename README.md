# Either add "sudo" before all commands or use "sudo su" first
# Amazon Linux 2023

#!/bin/bash
sudo su
dnf install git -y
git clone https://github.com/EasonNg0209/aws-assignment.git
cd aws-live
dnf install python-pip -y
pip3 install flask pymysql boto3 python-dotenv
python3 passing.py
