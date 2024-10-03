import json
from multiprocessing.connection import Client
import time
import threading
import psutil
import torch
import torchvision
import random

class RPCProxy:
    def __init__(self, connection):
        self._connection = connection

    def __getattr__(self, name):
        def do_rpc(*args, **kwargs):
            self._connection.send(json.dumps((name, args, kwargs)))
            return json.loads(self._connection.recv())
        return do_rpc

class Worker:
    def __init__(self, worker_id):
        self.worker_id = worker_id
        self.current_job = None
        self.job_progress = 0

    def get_status(self):
        return {
            'cpu_usage': psutil.cpu_percent(),
            'job_progress': self.job_progress
        }

    def run_job(self, job_id):
        self.current_job = job_id
        self.job_progress = 0
        
        # Simulate job progress
        total_steps = 10
        for step in range(total_steps):
            time.sleep(random.uniform(0.5, 1.5))  # Simulate work
            self.job_progress = (step + 1) / total_steps * 100
        
        result = f"Job {job_id} completed"
        self.current_job = None
        self.job_progress = 0
        return result

def worker_thread(worker, c):
    while True:
        func_name, args, kwargs = json.loads(c.recv())
        if func_name == 'get_status':
            c.send(json.dumps(worker.get_status()))
        elif func_name == 'run_job':
            result = worker.run_job(*args)
            c.send(json.dumps(result))
        else:
            c.send(json.dumps("Unknown function"))

if __name__ == '__main__':
    worker_id = f"worker_{id(threading.current_thread())}"
    worker = Worker(worker_id)
    
    c = Client(('localhost', 17000), authkey=b'peekaboo')
    proxy = RPCProxy(c)

    result = proxy.register_and_connect(worker_id) # Register and connect in one step
    print(result) 
    worker_thread(worker, c) # Start the worker thread to handle incoming requests