import json
from multiprocessing.connection import Listener
from threading import Thread, Lock
import time
from collections import deque
import sys

class WorkerInfo:
    def __init__(self, conn, worker_id):
        self.conn = conn
        self.id = worker_id
        self.cpu_usage = None
        self.lock = Lock()
        self.busy = False  # Track if worker is busy

class RPCHandler:
    def __init__(self):
        self.workers = {}  # stores WorkerInfo objects with worker_id as key. this is how we keep track of connected workers
        self.worker_id_counter = 0 # helps keeping track of total number of workers
        self.worker_lock = Lock() # used to synchronize access to workers and keeping threads organized
        self.pending_jobs = deque()  # Job queue
        self.job_counter = 0  # Keep track of total jobs assigned
        self.worker_index = 0  # For round-robin assignment

    def register_worker(self, connection):
        with self.worker_lock:
            worker_id = self.worker_id_counter # starts with 0
            self.worker_id_counter += 1 # increment worker_id_counter
            worker = WorkerInfo(connection, worker_id)  # instantiate new workerinfo object to save its details
            self.workers[worker_id] = worker # add worker to workers dictionary (we can have control over all the workers)
        print(f"Registered new worker with id {worker_id}")
        self.assign_jobs_from_queue() # try to assign any pending jobs in the queue to this new worker
        return worker

    def handle_connection(self, worker):
        conn = worker.conn # get the connection object from the worker
        try:
            while True:
                msg = conn.recv() # receive a message from the worker
                func_name, args, _ = json.loads(msg) # decode the message
                # We expect our workers to do two tasks: either report their status or execute a computation (which in this case is calculating π)
                if func_name == 'cpu_status':
                    with worker.lock: # lock the worker to prevent race conditions (if multiple threads try to access the same worker at the same time). this way we can keep everything in-place
                        worker.cpu_usage = args[0] # update the worker's cpu usage. we originally extract loadavg[['lavg_1', 'lavg_2', 'lavg_15']], but we only need lavg_1 (AVG of CPU usage in the last minute)
                    lavg_1 = worker.cpu_usage['lavg_1']
                    print(f"Received CPU usage from worker {worker.id}: AVG CPU Usage in the last minute = {lavg_1}")
                elif func_name == 'pi_result':
                    print(f"Received π result from worker {worker.id}: {args[0]}")
                    worker.busy = False
                #     # After receiving the result, try to assign more jobs
                #     self.assign_jobs_from_queue()
                # else:
                #     print(f"Unknown function {func_name} from worker {worker.id}")
        except EOFError:
            print(f"Worker {worker.id} disconnected")
            with self.worker_lock:
                del self.workers[worker.id] # remove the worker from workers dictionary if it disconnects
            pass

    def request_cpu_status(self, worker): 
        conn = worker.conn # get the connection object from the worker
        try:
            conn.send(json.dumps(('get_cpu_status', [], {}))) # send request to the worker to get its cpu status
        except Exception as e:
            print(f"Error requesting CPU status from worker {worker.id}: {e}") # print the error if the request fails

    def assign_compute_pi(self, worker):
        conn = worker.conn
        try:
            conn.send(json.dumps(('calculate_pi', [], {})))
            worker.busy = True # when assigning job, we set the worker status to busy
            print(f"Assigned compute_pi to worker {worker.id}")
        except Exception as e:
            print(f"Error assigning compute_pi to worker {worker.id}: {e}")
            worker.busy = False  # on error, we reset the worker status now it's going to be available again

    def monitor_workers(self):
        while True:
            with self.worker_lock:
                workers = list(self.workers.values())
            for worker in workers:
                self.request_cpu_status(worker)
            time.sleep(5)  # monitor worker cpu status every 5 seconds

    def assign_tasks(self, job_assigning_function = 'weighted_lb'):
        total_jobs = 20  # total number of jobs to assign
        while self.job_counter < total_jobs or self.pending_jobs:
            time.sleep(10) # wait 10 seconds and then assign a job if we haven't reached the total_jobs limit based on our assignment
            if self.job_counter < total_jobs:
                self.pending_jobs.append('calculate_pi')
                self.job_counter += 1
                print(f"Job {self.job_counter} added to the queue.")
            if job_assigning_function == 'round_robin_lb':
                self.assign_jobs_round_robin()
            if job_assigning_function == 'weighted_lb':
                self.assign_jobs_from_queue()
    
    def assign_jobs_round_robin(self):
        with self.worker_lock:
            if not self.workers:
                print("No workers connected.")
                return None
            idle_workers = [w for w in self.workers.values() if not w.busy]
            if not idle_workers:
                print("No idle workers available.")
                return None
            while self.pending_jobs and idle_workers:
                job = self.pending_jobs.popleft()
                # Round-robin selection
                selected_worker = idle_workers[self.worker_index % len(idle_workers)] # select the next idle worker based on the round-robin index
                self.worker_index += 1
                self.assign_compute_pi(selected_worker)

    def assign_jobs_from_queue(self):
        with self.worker_lock:
            if not self.workers:
                print("No workers connected.")
                return None
            # Get idle workers
            idle_workers = [w for w in self.workers.values() if not w.busy]
            if not idle_workers:
                print("No idle workers available.")
                return None
            while self.pending_jobs and idle_workers:
                # select the idle worker with the lowest CPU usage
                selected_worker = min(idle_workers, key=lambda w: float(w.cpu_usage['lavg_1']) if w.cpu_usage else float('inf')) # default to infinity if CPU usage is not available
                idle_workers.remove(selected_worker)
                job = self.pending_jobs.popleft()
                self.assign_compute_pi(selected_worker)

def rpc_server(handler, address, authkey):
    sock = Listener(address, authkey=authkey)
    while True:
        client = sock.accept()
        worker = handler.register_worker(client)
        t = Thread(target=handler.handle_connection, args=(worker,))
        t.daemon = True
        t.start()

if __name__ == '__main__':
    handler = RPCHandler()

    monitor_thread = Thread(target=handler.monitor_workers) # thread to monitor cpu usage
    monitor_thread.daemon = True # this runs in the background and does not prevent the program from closing when the main thread exits
    monitor_thread.start()
    
    load_balacing_algorithm = sys.argv[1] if len(sys.argv) > 1 else 'weighted_lb'
    assign_thread = Thread(target=handler.assign_tasks, args=(load_balacing_algorithm,)) # thread to assign jobs
    assign_thread.daemon = True # likewise
    assign_thread.start()

    # Run the server
    rpc_server(handler, ('10.128.0.2', 17000), authkey=b'peekaboo')