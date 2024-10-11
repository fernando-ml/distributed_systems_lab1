# Distributed Systems Lab1

This repository contains the code for Distributed Systems Lab1, implementing a simple distributed system with a server and multiple workers.

# Students
- Fernando Martinez
- Panayiotis Christou

## Prerequisites

- Python 3.x
- Git

## Installation

1. Clone the repository:

```sh
git clone https://github.com/fernando-ml/distributed_systems_lab1.git -b main
```

2. Navigate to the project directory:

```sh
cd distributed_systems_lab1
```

## Usage

To run the distributed system, execute the `start_lab1.sh` script in your terminal:

```sh
bash start_lab1.sh "{your server's internal IP address}" "{load balancing technique you want to utilize}"
```

Load balancing techniques supported are `weighted_lb` and `round_robin_lb`.

By default, the bash file takes ours (`default_ip="10.128.0.2"`, `default_algorithm="weighted_lb"`).

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

All required libraries are built-in Python modules, except for `matplotlib`, which will be installed automatically if missing for the server.

## Troubleshooting

If you encounter the error "_**VM's name does not contain 'server' or 'worker'**_", ensure that your VM names follow the naming convention described above.

## Output Files

The system generates graphs that are saved as PNG images. To download the generated graphs, you can use the following paths:

- `/home/{user}/distributed_systems_lab1/cpu_usage_distribution_weighted_lb.png`
- `/home/{user}/distributed_systems_lab1/cpu_vs_duration_weighted_lb.png`
- `/home/{user}/distributed_systems_lab1/job_durations_weighted_lb.png`
- `/home/{user}/distributed_systems_lab1/cpu_usage_distribution_round_robin_lb.png`
- `/home/{user}/distributed_systems_lab1/cpu_vs_duration_round_robin_lb.png`
- `/home/{user}/distributed_systems_lab1/job_durations_round_robin_lb.png`

Replace `{user}` with the username of the current machine.