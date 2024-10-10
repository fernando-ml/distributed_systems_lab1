hostname=$(hostname)

# install pip3 and matplotlib in case they are not installed
install_dependencies() {
    echo "Checking for pip3..."
    if ! command -v pip3 &> /dev/null; then
        echo "pip3 not found. Installing pip3..."
        sudo apt-get update
        sudo apt-get install -y python3-pip
    else
        echo "pip3 is already installed."
    fi

    echo "Checking for matplotlib..."
    if ! python3 -c "import matplotlib" &> /dev/null; then
        echo "matplotlib not found. Installing matplotlib..."
        pip3 install -U matplotlib
    else
        echo "matplotlib is already installed."
    fi
}

# verify if the hostname contains "server" or "worker"
if [[ $hostname == *"server"* ]]; then
    install_dependencies
    python3 server.py # run the server script
elif [[ $hostname == *"worker"* ]]; then
    python3 worker.py # execute the worker script
else
    echo "Error: VM's name does not contain 'server' or 'worker'"
    exit 1
fi