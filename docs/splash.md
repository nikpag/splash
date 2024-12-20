# SPLaSh docker setup

## Host

```sh
git clone git@github.com:binpash/pash.git
```

```sh
git checkout sls-eval
```

```sh
docker pull binpash/bash
```

```sh
docker run --platform linux/amd64 -d -v ~/pash:/pash --name pash binpash/pash:latest sleep infinity
```

Connect using terminal:

```sh
docker exec -it pash /bin/bash
```

Connect using VS Code:

```
Command Palette > Dev Containers: Attach to Running Container...
```

## Container

```sh
apt update
```

```sh
apt install vim
```

```sh
cat <<'EOF' >> ~/.bashrc
export PASH_TOP=/pash
export AWS_ACCOUNT_ID=637423169367
export AWS_BUCKET=nikpag20240414
export AWS_QUEUE=nikpag20240414
export LOG_FOLDER=$PASH_TOP/logs
EOF
```

```sh
source ~/.bashrc
```

```sh
cd ~
```

```sh
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
```

```sh
sudo apt install unzip
```

```sh
unzip awscliv2.zip
```

```sh
sudo ./aws/install
```

```sh
aws configure
```

```sh
sudo apt install python3-pip
```

```sh
sudo apt install python3-venv
```

```sh
python3 -m venv splash
```

```sh
source ~/splash/bin/activate
```

```sh
pip install boto3
```

```sh
/pash/scripts/distro-deps.sh
```

```sh
/pash/scripts/setup-pash.sh
```

```sh
/pash/runtime/serverless/binaries.sh
```

Deploy the stun repo according to the instructions, then use the `LayerVersionArn` you get from there to change the `serverless.yml` file of splash accordingly.

Then:

```sh
cd /pash/runtime/serverless/
```

```sh
sls deploy
```

# Bash benchmark EC2 setup

```sh
sudo apt update
```

```sh
cd /home/ubuntu
```

```sh
git clone https://github.com/binpash/pash.git
```

```sh
cd pash
```

```sh
git checkout sls-wip
```

```sh
cat <<EOF >> ~/.bashrc
export PASH_TOP=/pash
export AWS_ACCOUNT_ID=637423169367
export AWS_BUCKET=nikpag20240414
export AWS_QUEUE=nikpag20240414
EOF
```

```sh
source ~/.bashrc
```

```sh
cd /home/ubuntu
```

```sh
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
```

```sh
sudo apt install unzip
```

```sh
unzip awscliv2.zip
```

```sh
sudo ./aws/install
```

```sh
aws configure # default region name: us-east-1, default output format: json
```

```sh
sudo apt install python3-pip
```

```sh
sudo apt install python3-venv
```

```sh
python3 -m venv splash
```

```sh
source ~/splash/bin/activate
```

```sh
pip install boto3
```

For each benchmark suite:

```
./inputs.sh
```

```
./upload.sh
```

```
./run.sh
```
