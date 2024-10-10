hostname=$(hostname)

default_ip="10.128.0.2"
default_algorithm="weighted_lb"

# get command line arguments or use defaults
ip_address=${1:-$default_ip}
load_balancing_algorithm=${2:-$default_algorithm}

install_dependencies() {
    echo "Checking for pip3..."
    # install pip3 and matplotlib in case they are not installed
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
    python3 server.py "$ip_address" "$load_balancing_algorithm" # run the server script with arguments
elif [[ $hostname == *"worker"* ]]; then
    python3 worker.py "$ip_address" # execute the worker script
else
    echo "Error: VM's name does not contain 'server' or 'worker'"
    exit 1
fi