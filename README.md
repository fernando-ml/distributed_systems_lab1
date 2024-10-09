# Distributed Systems Lab1

This repository contains the code for Distributed Systems Lab1, implementing a simple distributed system with a server and multiple workers.

## Prerequisites

- Python 3.x
- Git

## Installation

1. Clone the repository:

```git clone https://github.com/fernando-ml/distributed_systems_lab1.git -b main```

2. Navigate to the project directory:

```cd distributed_systems_lab1```

## Usage

To run the distributed system, execute the `start_lab1.sh` script in your terminal:


```bash start_lab1.sh```

### Important Naming Convention

- Name your manager virtual machine (VM) with "server" in its name (e.g., "server", "main_server").
- Name your worker VMs with "worker" in their names (e.g., "worker1", "worker2", "worker_1", "worker_2").

This naming convention is crucial as the script uses it to determine which Python file to run on each VM.

## How It Works

The `start_lab1.sh` script does the following:

1. Clones the repository (if running for the first time).
2. Checks the hostname of the current machine.
3. Based on the hostname:
   - If it contains "server", it runs `server.py`.
   - If it contains "worker", it runs `worker.py`.
   - If neither, it displays an error message.

## Dependencies

All required libraries are built-in Python modules. No additional installations are necessary.

## Troubleshooting

If you encounter the error "_**VM's name does not contain 'server' or 'worker'**_", ensure that your VM names follow the naming convention described above.
