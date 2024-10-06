# manager.py
import json
import time
from multiprocessing.connection import Listener
from threading import Thread, Lock
import heapq

class RPCHandler:
    def __init__(self):
        self._functions = {}

    def register_function(self, func):
        self._functions[func.__name__] = func

    def handle_connection(self, connection):
        try:
            while True:
                try:
                    data = connection.recv()
                    func_name, args, kwargs = json.loads(data)
                    # Ensure the received data is valid
                    if func_name in self._functions:
                        r = self._functions[func_name](*args, **kwargs)
                        connection.send(json.dumps(r))
                    else:
                        connection.send(json.dumps(f"Unknown function: {func_name}"))
                except (EOFError, ConnectionError) as e:
                    print(f"Worker disconnected or communication error: {e}")
                    break
                except json.JSONDecodeError as e:
                    print(f"Invalid data received from worker: {e}")
                    connection.send(json.dumps("Error: Invalid data format"))
        except Exception as e:
            print(f"Unexpected error in handling connection: {e}")

class WorkerManager:
    def __init__(self):
        self.workers = {}
        self.lock = Lock()
        self.job_queue = []

    def add_worker(self, worker_id, connection):
        with self.lock:
            self.workers[worker_id] = {
                'connection': connection,
                'status': 'idle',
                'cpu_usage': 0,
                'job_progress': 0
            }

    def remove_worker(self, worker_id):
        with self.lock:
            if worker_id in self.workers:
                del self.workers[worker_id]

    def update_worker_status(self, worker_id, status, cpu_usage, job_progress):
        with self.lock:
            if worker_id in self.workers:
                self.workers[worker_id]['status'] = status
                self.workers[worker_id]['cpu_usage'] = cpu_usage
                self.workers[worker_id]['job_progress'] = job_progress

    def get_idle_worker(self):
        with self.lock:
            idle_workers = [w for w in self.workers.items() if w[1]['status'] == 'idle']
            if idle_workers:
                #Put algorithm logic for choosing worker here
                return min(idle_workers, key=lambda x: x[1]['cpu_usage'])[0]
        return None

    def assign_job(self, job):
        worker_id = self.get_idle_worker()
        if worker_id:
            worker = self.workers[worker_id]
            try:
                worker['connection'].send(json.dumps(('run_job', [job], {})))
                worker['status'] = 'busy'
                print('Assigned job', job, 'to worker', worker_id, flush=True)
                return True
            except (EOFError, ConnectionError) as e:
                print(f"Failed to assign job {job} to worker {worker_id}: {e}")
                self.remove_worker(worker_id)
        return False

    def monitor_workers(self):
        while True:
            time.sleep(5)
            with self.lock:
                for worker_id, worker in list(self.workers.items()):
                    try:
                        # Send the status request to the worker
                        worker['connection'].send(json.dumps(('get_status', [], {})))
                        # Receive the response
                        response = worker['connection'].recv()
                        print(f"Raw response from worker {worker_id}: {response}", flush=True)  # Debug print

                        # Try to parse the response
                        try:
                            status, cpu_usage, job_progress = json.loads(response)
                        except (json.JSONDecodeError, ValueError) as e:
                            print(f"Error decoding response from worker {worker_id}: {e}", flush=True)
                            self.remove_worker(worker_id)
                            continue

                        # Update worker status if parsing is successful
                        self.update_worker_status(worker_id, status, cpu_usage, job_progress)
                        print(f'Worker {worker_id}: {status}, CPU: {cpu_usage}%, Progress: {job_progress}%', flush=True)

                    except (EOFError, ConnectionError) as e:
                        print(f"Worker {worker_id} disconnected or failed: {e}", flush=True)
                        self.remove_worker(worker_id)



    def load_balancer(self):
        while True:
            if self.job_queue:
                job = heapq.heappop(self.job_queue)
                if not self.assign_job(job):
                    # print(f'No available workers, putting job {job} back in queue')
                    heapq.heappush(self.job_queue, job)
            time.sleep(1)

def rpc_server(handler, address, authkey):
    sock = Listener(address, authkey=authkey)
    worker_manager = WorkerManager()
    
    monitor_thread = Thread(target=worker_manager.monitor_workers)
    monitor_thread.daemon = True
    monitor_thread.start()

    load_balancer_thread = Thread(target=worker_manager.load_balancer)
    load_balancer_thread.daemon = True
    load_balancer_thread.start()
    
    # Adding 20 jobs to the queue
    for i in range(20):
        job = f"Job-{i+1}"
        heapq.heappush(worker_manager.job_queue, job)
        print(f"Added {job} to the job queue.")

    worker_id = 0
    while True:
        client = sock.accept()
        worker_id += 1
        worker_manager.add_worker(worker_id, client)
        t = Thread(target=handler.handle_connection, args=(client,))
        t.daemon = True
        t.start()

# Register functions
handler = RPCHandler()
handler.register_function(lambda x, y: x + y)  # Simple add function for testing

# Run the server
if __name__ == '__main__':
    rpc_server(handler, ('10.128.0.2', 17000), authkey=b'peekaboo')
