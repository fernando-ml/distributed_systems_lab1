import json
from multiprocessing.connection import Listener
from threading import Thread, Lock
import time
import queue

class RPCHandler:
    def __init__(self):
        self._functions = {}
        self.workers = {}
        self.jobs = queue.Queue()
        self.job_counter = 0
        self.round_robin_index = 0  # For round-robin algorithm
        self.load_balancing = True  # Flag to switch between algorithms
        self.connection_locks = {}  # Mapping from worker_id to Lock

    def register_function(self, func):
        self._functions[func.__name__] = func

    def connect_worker(self, worker_id, connection):
        if worker_id in self.workers:
            self.workers[worker_id]['connection'] = connection
            self.connection_locks[worker_id] = Lock()
            return f"Worker {worker_id} connected successfully"
        else:
            return f"Worker {worker_id} not registered"

    def register_worker(self, worker_id, address):
        if worker_id not in self.workers:
            self.workers[worker_id] = {
                'id': worker_id,
                'address': address,
                'connection': None,
                'status': {'cpu_usage': 0, 'job_progress': 0},
                'current_job': None
            }
            return f"Worker {worker_id} registered successfully"
        else:
            return f"Worker {worker_id} is already registered"

    def handle_connection(self, connection):
        try:
            while True:
                data = connection.recv()
                message = json.loads(data)
                
                # Validate message structure
                if isinstance(message, (list, tuple)) and len(message) == 3:
                    func_name, args, kwargs = message
                    if func_name == 'register_and_connect':
                        worker_id = args[0]
                        address = kwargs.get('address')
                        result = self.register_worker(worker_id, address)
                        result += ". " + self.connect_worker(worker_id, connection)
                        connection.send(json.dumps(("ack", [result], {})))
                    elif func_name == 'job_completed':
                        worker_id = args[0]
                        job_id = args[1]
                        self.job_completed(worker_id, job_id)
                        connection.send(json.dumps(("ack", ["Job completion acknowledged"], {})))
                    else:
                        try:
                            if func_name in self._functions:
                                r = self._functions[func_name](*args, **kwargs)
                                connection.send(json.dumps((func_name + "_response", [r], {})))
                            else:
                                connection.send(json.dumps(("error", [f"Function {func_name} not registered"], {})))
                        except Exception as e:
                            connection.send(json.dumps(("error", [str(e)], {})))
                else:
                    # Handle unexpected message formats gracefully
                    print(f"Invalid message format received: {message}")
                    connection.send(json.dumps(("error", ["Invalid message format"], {})))
        except EOFError:
            print("Connection closed")
        except Exception as e:
            print(f"Error in handle_connection: {e}")

    def print_worker_status(self):
        print("\n--- Worker Status ---")
        for worker_id, worker in self.workers.items():
            status = worker.get('status', {})
            print(f"Worker {worker_id}:")
            print(f"  CPU Usage: {status.get('cpu_usage', 'N/A')}%")
            print(f"  Job Progress: {status.get('job_progress', 'N/A')}%")
            print(f"  Current Job: {worker.get('current_job', 'None')}")
        print("---------------------\n")

    def monitor_resources(self):
        while True:
            for worker_id, worker in self.workers.items():
                if worker['connection']:
                    try:
                        with self.connection_locks[worker_id]:
                            # Request status from worker
                            worker['connection'].send(json.dumps(("get_status", [], {})))
                            status = json.loads(worker['connection'].recv())
                            if isinstance(status, dict):
                                worker['status'] = status
                            else:
                                print(f"Received invalid status from {worker_id}: {status}")
                    except Exception as e:
                        print(f"Error communicating with {worker_id}: {e}")
            self.print_worker_status()  # Print status after updating
            time.sleep(5)

    def assign_workload(self):
        while True:
            try:
                job = self.jobs.get(timeout=1)  # Wait for a job
                worker = self.select_worker()
                if worker:
                    print(f"Assigning job {job} to worker {worker['id']}")
                    with self.connection_locks[worker['id']]:
                        worker['connection'].send(json.dumps(("run_job", [job], {})))
                    worker['current_job'] = job
                else:
                    print("No available workers, putting job back in queue")
                    self.jobs.put(job)
            except queue.Empty:
                pass  # No job to assign
            time.sleep(0.1)

    def select_worker(self):
        available_workers = [w for w in self.workers.values() if w['status'].get('job_progress', 0) == 0]
        if not available_workers:
            return None

        if self.load_balancing:
            # Select worker with the lowest CPU usage
            selected_worker = min(available_workers, key=lambda w: w['status'].get('cpu_usage', 0))
            return selected_worker
        else:
            # Round-robin selection
            worker_ids = sorted(self.workers.keys())
            if not worker_ids:
                return None
            worker_id = worker_ids[self.round_robin_index % len(worker_ids)]
            self.round_robin_index += 1
            return self.workers[worker_id]

    def submit_jobs(self, total_jobs, interval_seconds):
        for _ in range(total_jobs):
            job_id = f"job_{self.job_counter}"
            self.jobs.put(job_id)
            print(f"Submitted {job_id}")
            self.job_counter += 1
            time.sleep(interval_seconds)

    def job_completed(self, worker_id, job_id):
        if worker_id in self.workers:
            self.workers[worker_id]['current_job'] = None
            print(f"Job {job_id} completed by Worker {worker_id}")
        else:
            print(f"Received completion from unknown Worker {worker_id}")

def register_worker(worker_id, address):
    return handler.register_worker(worker_id, address)

def connect_worker(worker_id, connection):
    return handler.connect_worker(worker_id, connection)

def add_job(job_id):
    handler.jobs.put(job_id)
    return f"Job {job_id} added successfully"

def job_completed(worker_id, job_id):
    handler.job_completed(worker_id, job_id)

handler = RPCHandler()
handler.register_function(register_worker)
handler.register_function(connect_worker)
handler.register_function(add_job)
handler.register_function(job_completed)

def rpc_server(handler, address, authkey):
    sock = Listener(address, authkey=authkey)
    print(f"Server listening on {address}")
    while True:
        client = sock.accept()
        print(f"Connection accepted from {client}")
        t = Thread(target=handler.handle_connection, args=(client,))
        t.daemon = True
        t.start()

if __name__ == '__main__':
    # Start resource monitoring thread
    Thread(target=handler.monitor_resources, daemon=True).start()
    # Start workload assignment thread
    Thread(target=handler.assign_workload, daemon=True).start()
    # Start RPC server
    server_thread = Thread(target=rpc_server, args=(handler, ('0.0.0.0', 17000), b'peekaboo'), daemon=True)
    server_thread.start()

    # Submit 20 jobs with 10-second intervals
    total_jobs = 2
    interval_seconds = 10
    print(f"Submitting {total_jobs} jobs with {interval_seconds}-second intervals...")
    handler.submit_jobs(total_jobs, interval_seconds)

    # Optionally, switch to round-robin after some time or based on user input
    # For demonstration, we'll switch after all jobs are submitted
    handler.load_balancing = False
    print("Switched to Round-Robin load balancing.")

    # Keep the main thread alive
    while True:
        time.sleep(1)