import sys
import json
from threading import Thread
from multiprocessing.connection import Client
from monitor_lib import get_cpu_status
from pi_calculation import calculate_pi_leibniz
import time

class Worker:
    def __init__(self, address, authkey):
        self.connection = Client(address, authkey=authkey)

    def send_cpu_status(self):
        cpu_status = get_cpu_status()  # get CPU status from monitor_lib
        self.connection.send(json.dumps(('cpu_status', [cpu_status], {})))  # send CPU status to server

    def handle_server_messages(self):
        try:
            while True:
                msg = self.connection.recv()  # receive message from server
                func_name, args, _ = json.loads(msg)  # decode message
                if func_name == 'get_cpu_status':
                    self.send_cpu_status()
                elif func_name == 'calculate_pi':
                    job_id = args[0]  # get the job ID
                    t = Thread(target=self.calculate_pi, args=(job_id,))
                    t.daemon = True
                    t.start()
                else:
                    print(f"Unknown function {func_name}")
        except EOFError:
            print("Disconnected from server.")
            pass

    def calculate_pi(self, job_id):
        result = calculate_pi_leibniz()
        self.connection.send(json.dumps(('pi_result', [job_id, result], {})))

    def start(self):
        t = Thread(target=self.handle_server_messages)  # thread to handle messages from the server
        t.daemon = True
        t.start()
        while True:  # keep the main thread running
            time.sleep(1)

if __name__ == '__main__':
    server_internal_ip = sys.argv[1] if len(sys.argv) > 1 else '10.128.0.2'
    worker = Worker(('10.128.0.2', 17000), authkey=b'peekaboo')
    worker.start()