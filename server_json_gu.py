import json
from multiprocessing.connection import Listener
from threading import Thread, Lock
import time
from collections import deque

class WorkerInfo:
    def __init__(self, conn, worker_id):
        self.conn = conn
        self.id = worker_id
        self.cpu_usage = None
        self.lock = Lock()
        self.busy = False  # Track if worker is busy

class RPCHandler:
    def __init__(self):
        self.workers = {}  # Stores WorkerInfo objects with worker_id as key
        self.worker_id_counter = 0
        self.worker_lock = Lock()
        self.pending_jobs = deque()  # Job queue
        self.job_counter = 0  # Keep track of total jobs assigned
        self.worker_index = 0  # For round-robin assignment

    def register_worker(self, connection):
        with self.worker_lock:
            worker_id = self.worker_id_counter
            self.worker_id_counter += 1
            worker = WorkerInfo(connection, worker_id)
            self.workers[worker_id] = worker
        print(f"Registered new worker with id {worker_id}")
        # Try to assign any pending jobs to this new worker
        self.assign_jobs_from_queue()
        return worker

    def handle_connection(self, worker):
        conn = worker.conn
        try:
            while True:
                # Receive a message from the worker
                msg = conn.recv()
                func_name, args, kwargs = json.loads(msg)
                # Handle different functions
                if func_name == 'cpu_status':
                    with worker.lock:
                        worker.cpu_usage = args[0]
                    lavg_1 = worker.cpu_usage['lavg_1']
                    print(f"Received CPU usage from worker {worker.id}: lavg_1 = {lavg_1}")
                elif func_name == 'pi_result':
                    print(f"Received π result from worker {worker.id}: {args[0]}")
                    worker.busy = False
                    # After receiving the result, try to assign more jobs
                    self.assign_jobs_from_queue()
                else:
                    print(f"Unknown function {func_name} from worker {worker.id}")
        except EOFError:
            print(f"Worker {worker.id} disconnected")
            with self.worker_lock:
                del self.workers[worker.id]
            pass

    def request_cpu_status(self, worker):
        conn = worker.conn
        try:
            conn.send(json.dumps(('get_cpu_status', [], {})))
        except Exception as e:
            print(f"Error requesting CPU status from worker {worker.id}: {e}")

    def assign_compute_pi(self, worker):
        conn = worker.conn
        try:
            conn.send(json.dumps(('calculate_pi', [], {})))
            worker.busy = True # when assigning job, we set the worker status to busy
            print(f"Assigned compute_pi to worker {worker.id}")
        except Exception as e:
            print(f"Error assigning compute_pi to worker {worker.id}: {e}")
            worker.busy = False  # on error, we reset the worker status

    def monitor_workers(self):
        while True:
            with self.worker_lock:
                workers = list(self.workers.values())
            for worker in workers:
                self.request_cpu_status(worker)
            time.sleep(5)  # monitor worker cpu status every 5 seconds

    def assign_tasks(self):
        total_jobs = 20  # total number of jobs to assign
        while self.job_counter < total_jobs or self.pending_jobs:
            time.sleep(10) # wait 10 seconds and then assign a job if we haven't reached the total_jobs limit based on our assignment
            if self.job_counter < total_jobs:
                self.pending_jobs.append('calculate_pi')
                self.job_counter += 1
                print(f"Job {self.job_counter} added to the queue.")
            # Try to assign jobs from the queue
            self.assign_jobs_from_queue()

    def assign_jobs_from_queue(self):
        with self.worker_lock:
            if not self.workers:
                print("No workers connected.")
                return
            # Get idle workers
            idle_workers = [w for w in self.workers.values() if not w.busy]
            if not idle_workers:
                print("No idle workers available.")
                return
            while self.pending_jobs and idle_workers:
                # select the idle worker with the lowest CPU usage
                selected_worker = min(
                    idle_workers,
                    key=lambda w: float(w.cpu_usage['lavg_1']) if w.cpu_usage else float('inf')
                )
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
    monitor_thread.daemon = True
    monitor_thread.start()

    assign_thread = Thread(target=handler.assign_tasks) # thread to assign jobs
    assign_thread.daemon = True
    assign_thread.start()

    # Run the server
    rpc_server(handler, ('10.128.0.2', 17000), authkey=b'peekaboo')