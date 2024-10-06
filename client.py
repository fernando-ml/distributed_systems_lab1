from multiprocessing.connection import Client
import json
import time

class RPCProxy:
    def __init__(self, connection):
        self._connection = connection

    def __getattr__(self, name):
        def do_rpc(*args, **kwargs):
            self._connection.send(json.dumps((name, args, kwargs)))
            return json.loads(self._connection.recv())
        return do_rpc

if __name__ == '__main__':
    c = Client(('localhost', 17000), authkey=b'peekaboo')
    proxy = RPCProxy(c)

    # Launch 20 computing jobs with a 10-second interval
    for i in range(20):
        job_id = f"job_{i}"
        result = proxy.add_job(job_id)
        print(result)
        time.sleep(10)