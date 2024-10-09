import json
from threading import Thread
from multiprocessing.connection import Client
from monitor_lib import get_cpu_status
from pi_calculation import calculate_pi_leibniz
import time

class Worker:
    def __init__(self, address, authkey):
        self.connection = Client(address, authkey=authkey)
        self.job_progress = 0
        self.calculating_pi = False # flag to indicate if the worker is currently calculating π

    def send_cpu_status(self):
        cpu_status = get_cpu_status() # get CPU status from monitor_lib
        self.connection.send(json.dumps(('cpu_status', [cpu_status], {}))) # send CPU status to server

    def handle_server_messages(self):
        try:
            while True:
                msg = self.connection.recv() # receive message from server
                func_name, _, _ = json.loads(msg) # decode message 
                if func_name == 'get_cpu_status':
                    self.send_cpu_status()
                elif func_name == 'calculate_pi':
                    if not self.calculating_pi:
                        t = Thread(target=self.calculate_pi) # thread to calculate π
                        t.daemon = True
                        t.start()
                    else:
                        print("Already calculating π.")
                else:
                    print(f"Unknown function {func_name}")
        except EOFError:
            print("Disconnected from server.")
            pass

    def calculate_pi(self):
        self.calculating_pi = True
        result = calculate_pi_leibniz()
        self.connection.send(json.dumps(('pi_result', [result], {})))
        self.calculating_pi = False

if __name__ == '__main__':
    worker = Worker(('10.128.0.2', 17000), authkey=b'peekaboo')

    
    t = Thread(target=worker.handle_server_messages) #  thread to handle messages from the server
    t.daemon = True
    t.start()

    while True: # to keep the main thread running
        time.sleep(1)