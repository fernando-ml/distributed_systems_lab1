import json
from multiprocessing.connection import Listener
from threading import Thread
import time

class RPCHandler:
    def __init__(self):
        self._functions = {}
        self.workers = {}
        self.jobs = []
        self.job_counter = 0

    def register_function(self, func):
        self._functions[func.__name__] = func

    def handle_connection(self, connection):
        try:
            while True:
                func_name, args, kwargs = json.loads(connection.recv())
                if func_name == 'register_and_connect':
                    worker_id = args[0]
                    result = self.connect_worker(worker_id, connection)
                    connection.send(json.dumps(result))
                else:
                    try:
                        r = self._functions[func_name](*args, **kwargs)
                        connection.send(json.dumps(r))
                    except Exception as e:
                        connection.send(json.dumps(str(e)))
        except EOFError:
            pass

    def monitor_resources(self):
        while True:
            for worker_id, worker in self.workers.items():
                worker['connection'].send(json.dumps(('get_status', [], {})))
                status = json.loads(worker['connection'].recv())
                self.workers[worker_id]['status'] = status
            time.sleep(5)

    def assign_workload(self):
        while True:
            if self.jobs:
                job = self.jobs.pop(0)
                worker = self.select_worker()
                worker['connection'].send(json.dumps(('run_job', [job], {})))
                result = json.loads(worker['connection'].recv())
                print(f"Job {job} assigned to {worker['id']}")
            time.sleep(1)

    def select_worker(self):
        # Load balancing algorithm
        available_workers = [w for w in self.workers.values() if w['status']['job_progress'] == 0]
        if available_workers:
            return min(available_workers, key=lambda w: w['status']['cpu_usage'])
        else:
            return min(self.workers.values(), key=lambda w: w['status']['cpu_usage'] * (1 + w['status']['job_progress']))

def register_worker(worker_id, address):
    handler.workers[worker_id] = {'id': worker_id, 'address': address, 'status': {'cpu_usage': 0, 'job_progress': 0}, 'connection': None}
    return "Worker registered successfully"

def connect_worker(worker_id, connection):
    worker = handler.workers[worker_id]
    worker['connection'] = connection
    return "Worker connected successfully"

def add_job(job_id):
    handler.jobs.append(job_id)
    return f"Job {job_id} added successfully"

handler = RPCHandler()
handler.register_function(register_worker)
handler.register_function(connect_worker)
handler.register_function(add_job)

def rpc_server(handler, address, authkey):
    sock = Listener(address, authkey=authkey)
    while True:
        client = sock.accept()
        t = Thread(target=handler.handle_connection, args=(client,))
        t.daemon = True
        t.start()

if __name__ == '__main__':
    Thread(target=handler.monitor_resources, daemon=True).start()
    Thread(target=handler.assign_workload, daemon=True).start()
    rpc_server(handler, ('localhost', 17000), authkey=b'peekaboo')