import json
from multiprocessing.connection import Listener
from threading import Thread, Lock
import time
import os
import sys
from plot_utils import generate_plots # import the generate_plots function
from time import perf_counter

class WorkerInfo:
    def __init__(self, conn, worker_id):
        self.conn = conn
        self.id = worker_id
        self.cpu_usage = None
        self.lock = Lock()

class RPCHandler:
    def __init__(self, load_balancing_algorithm='weighted_lb'):
        self.workers = {}  # Stores WorkerInfo objects with worker_id as key
        self.worker_id_counter = 0  # Helps keep track of total number of workers
        self.worker_lock = Lock()  # Synchronizes access to workers and manage them independently
        self.job_counter, self.worker_index = 0, 0  # Keep track of total jobs assigned and worker index for round-robin assignment
        self.load_balancing_algorithm = load_balancing_algorithm  # Load balancing algorithm
        self.job_assignments = []  # List to store job assignment logs
        self.job_completions = []  # List to store job completion logs
        self.assignment_log_filename = f"assignment_log_{self.load_balancing_algorithm}.json"
        self.completion_log_filename = f"completion_log_{self.load_balancing_algorithm}.json"
        self.starting_time = perf_counter()

    def register_worker(self, connection):
        with self.worker_lock:
            worker_id = self.worker_id_counter  # assign a unique worker ID
            self.worker_id_counter += 1
            worker = WorkerInfo(connection, worker_id)  # Create a new WorkerInfo object
            self.workers[worker_id] = worker  # add worker to the workers dictionary
        print(f"Registered new worker with id {worker_id}")
        return worker

    def handle_connection(self, worker):
        conn = worker.conn  # get the connection object from the worker
        try:
            while True:
                msg = conn.recv()  # receive a message from the worker
                func_name, args, _ = json.loads(msg)  # decode the message
                # deal with different functions
                if func_name == 'cpu_status':
                    with worker.lock:  # lock the worker to prevent race conditions
                        worker.cpu_usage = args[0]  # Update the worker's CPU usage
                    lavg_1 = worker.cpu_usage['lavg_1']
                    print(f"Received CPU usage from worker {worker.id}: AVG CPU Usage in the last minute = {lavg_1}")
                elif func_name == 'pi_result':
                    job_id, result = args
                    timestamp = time.time()
                    completion = {
                        'time_completed': timestamp,
                        'worker_id': worker.id,
                        'job_id': job_id,
                        'result': result
                    }
                    self.job_completions.append(completion)
                    print(f"Received π result from worker {worker.id} (Job ID: {job_id}): {result}")
                else:
                    print(f"Unknown function {func_name} from worker {worker.id}")
        except EOFError:
            print(f"Worker {worker.id} disconnected")
            with self.worker_lock:
                del self.workers[worker.id]  # remove the worker from the workers dictionary
            pass

    def request_cpu_status(self, worker):
        conn = worker.conn  # get the connection object from the worker
        try:
            conn.send(json.dumps(('get_cpu_status', [], {})))  # request CPU status from the worker
        except Exception as e:
            print(f"Error requesting CPU status from worker {worker.id}: {e}")

    def assign_compute_pi(self, worker, job_id):
        conn = worker.conn
        try:
            conn.send(json.dumps(('calculate_pi', [job_id], {})))  # send the job ID to the worker
            timestamp = time.time()
            lavg_1 = float(worker.cpu_usage['lavg_1']) if worker.cpu_usage else None
            assignment = {
                'time_assigned': timestamp,
                'worker_id': worker.id,
                'cpu_usage': lavg_1,
                'load_balancing': self.load_balancing_algorithm,
                'job_id': job_id
            }
            self.job_assignments.append(assignment)
            print(f"Assigned PI Computation to worker {worker.id} (Job ID: {job_id})")
        except Exception as e:
            print(f"Error assigning PI Computation to worker {worker.id}: {e}")

    def monitor_workers(self):
        while True:
            with self.worker_lock:
                workers = list(self.workers.values())
            for worker in workers:
                self.request_cpu_status(worker)
            time.sleep(5)  # Monitor worker CPU status every 5 seconds

    def assign_tasks(self):
        total_jobs = 20  # total number of jobs to assign
        jobs_assigned = 0 # counter of number of jobs assigned so far
        while jobs_assigned < total_jobs:
            time.sleep(5)  # wait 5 seconds between job assignments
            if self.load_balancing_algorithm == 'round_robin_lb':
                assigned = self.assign_job_round_robin() 
            elif self.load_balancing_algorithm == 'weighted_lb':
                assigned = self.assign_job_weighted()
            else:
                print(f"Unknown load balancing algorithm: {self.load_balancing_algorithm}")
                break
            if assigned:
                jobs_assigned += 1
                print(f"Job {self.job_counter} assigned.")
            else:
                print("No worker available to assign job.")

    def assign_job_round_robin(self): # assign jobs to workers in a round-robin manner
        with self.worker_lock:
            if not self.workers:
                print("No workers connected.")
                return False
            worker_ids = list(self.workers.keys())
            worker_id = worker_ids[self.worker_index % len(worker_ids)] # assign jobs based on worker index
            selected_worker = self.workers[worker_id]
            self.worker_index += 1
            self.job_counter += 1
            self.assign_compute_pi(selected_worker, self.job_counter)
            return True

    def assign_job_weighted(self):
        with self.worker_lock:
            if not self.workers:
                print("No workers connected.")
                return False
            available_workers = list(self.workers.values())
            # select the worker with the lowest CPU usage
            selected_worker = min(available_workers, key=lambda w: float(w.cpu_usage['lavg_1']) if w.cpu_usage else float('inf'))
            self.job_counter += 1
            self.assign_compute_pi(selected_worker, self.job_counter)
            return True

    def monitor_completion(self):
        total_jobs = 20
        while len(self.job_completions) < total_jobs:
            time.sleep(10)  # wait for job completions
        print("All jobs completed.")
        # save and update log files
        with open(self.assignment_log_filename, 'w') as f:
            json.dump(self.job_assignments, f)
        with open(self.completion_log_filename, 'w') as f:
            json.dump(self.job_completions, f)
        print(f"Logs saved to {self.assignment_log_filename} and {self.completion_log_filename}.")
        # Generate plots
        generate_plots(self.job_assignments, self.job_completions, self.load_balancing_algorithm)
        print("Plots generated.")
        end_time = perf_counter()
        print(f"Total time taken: {end_time - self.starting_time:.2f} seconds")
        os._exit(0) # stop server after finishing jobs

def rpc_server(handler, address, authkey):
    sock = Listener(address, authkey=authkey) # create a socket
    while True:
        client = sock.accept() # accept a connection
        worker = handler.register_worker(client) # register the worker
        t = Thread(target=handler.handle_connection, args=(worker,)) # create a thread to handle the connection
        t.daemon = True
        t.start()

if __name__ == '__main__':
    server_internal_ip = sys.argv[1] if len(sys.argv) > 1 else '10.128.0.2'
    load_balancing_algorithm = sys.argv[2] if len(sys.argv) > 2 else 'weighted_lb'

    handler = RPCHandler(load_balancing_algorithm=load_balancing_algorithm)

    monitor_thread = Thread(target=handler.monitor_workers) # thread to monitor CPU usage
    monitor_thread.daemon = True
    monitor_thread.start()

    assign_thread = Thread(target=handler.assign_tasks) # thread to assign jobs
    assign_thread.daemon = True
    assign_thread.start()

    completion_thread = Thread(target=handler.monitor_completion) # thread to monitor job completions
    completion_thread.start() # not daemon because it needs to run until all jobs are completed

    rpc_server(handler, (server_internal_ip, 17000), authkey=b'peekaboo') # run the server