# pull the GitHub repository
git clone https://github.com/fernando-ml/distributed_systems_lab1.git -b main
cd distributed_systems_lab1

hostname=$(hostname)

# verify if the hostname contains "server" or "worker"
if [[ $hostname == *"server"* ]]; then
    python3 server.py
elif [[ $hostname == *"worker"* ]]; then
    python3 worker.py
else
    echo "Error: VM's name does not contain 'server' or 'worker'"
    exit 1
fi