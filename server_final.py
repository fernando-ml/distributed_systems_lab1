import json
import socket
from threading import Thread
from multiprocessing.connection import Listener
import time


class RPCHandler:
    def __init__(self):
        self._functions = {}
        self.workers = {}
        self.jobs = []
    
    def register_function(self, func):
        self._functions[func.__name__] = func

    def connect_worker(self, worker_id, connection):
        if worker_id in self.workers:
            self.workers[worker_id]['connection'] = connection
            return f"Worker {worker_id} connected successfully"
        else:
            return f"Worker {worker_id} not registered"
    def handle_connection(self, connection):
        try:
            while True:
                # Receive a message
                func_name, args, kwargs = json.loads(connection.recv())
                # Run the RPC and send a response
                try:
                    r = self._functions[func_name](*args,**kwargs)
                    connection.send(json.dumps(r))
                except Exception as e:
                    connection.send(json.dumps(str(e)))
        except EOFError:
             pass
    

    
def rpc_server(handler, address, authkey):
    sock = Listener(address, authkey=authkey)
    while True:
        client = sock.accept()
        # Multiple threading
        t = Thread(target=handler.handle_connection, args=(client,))
        t.daemon = True
        t.start()

handler = RPCHandler()
rpc_server(handler, ('localhost', 17000), authkey=b'peekaboo')