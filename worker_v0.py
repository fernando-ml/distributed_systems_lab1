# worker.py
import json
import time
from multiprocessing.connection import Client
from monitor_lib import get_cpu_status
from pi_calculation import calculate_pi_leibniz

class RPCProxy:
    def __init__(self, connection):
        self._connection = connection

    def __getattr__(self, name):
        def do_rpc(*args, **kwargs):
            self._connection.send(json.dumps((name, args, kwargs)))
            result = json.loads(self._connection.recv())
            return result
        return do_rpc

class Worker:
    def __init__(self, connection):
        self.proxy = RPCProxy(connection)
        self.status = 'idle'
        self.job_progress = 0

    def get_status(self):
        cpu_usage = float(get_cpu_status()['lavg_1'])
        return self.status, cpu_usage, self.job_progress

    def run_job(self, job_id):
        self.status = 'busy'
        self.job_progress = 0
        
        print(f"Starting job {job_id}")
        
        pi_value = calculate_pi_leibniz(self.job_progress)
        
        self.status = 'idle'
        print(f"Job {job_id} completed")

def main():
    connection = Client(('10.128.0.2', 17000), authkey=b'peekaboo')
    worker = Worker(connection)
    
    while True:
        func_name, args, _ = json.loads(connection.recv())
        if func_name == 'get_status':
            result = worker.get_status()
        elif func_name == 'run_job':
            worker.run_job(args[0])
            result = "Job completed"
        else:
            result = f"Unknown function: {func_name}"
        connection.send(json.dumps(result))

if __name__ == '__main__':
    main()
