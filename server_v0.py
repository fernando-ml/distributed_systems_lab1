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
                func_name, args, kwargs = json.loads(connection.recv())
                try:
                    r = self._functions[func_name](*args, **kwargs)
                    connection.send(json.dumps(r))
                except Exception as e:
                    connection.send(json.dumps(str(e)))
        except EOFError:
            pass

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
                return min(idle_workers, key=lambda x: x[1]['cpu_usage'])[0]
        return None

    def assign_job(self, job):
        worker_id = self.get_idle_worker()
        if worker_id:
            worker = self.workers[worker_id]
            worker['connection'].send(json.dumps(('run_job', [job], {})))
            worker['status'] = 'busy'
            return True
        return False

    def monitor_workers(self):
        while True:
            time.sleep(5)
            with self.lock:
                for worker_id, worker in self.workers.items():
                    worker['connection'].send(json.dumps(('get_status', [], {})))
                    status, cpu_usage, job_progress = json.loads(worker['connection'].recv())
                    self.update_worker_status(worker_id, status, cpu_usage, job_progress)

    def load_balancer(self):
        while True:
            if self.job_queue:
                job = heapq.heappop(self.job_queue)
                if not self.assign_job(job):
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
    rpc_server(handler, ('localhost', 17000), authkey=b'peekaboo')