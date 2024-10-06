import json
from multiprocessing.connection import Client
from monitor_lib import get_cpu_status
from pi_calculation import calculate_pi_leibniz

class RPCProxy:
    def __init__(self, connection):
        self._connection = connection

    def __getattr__(self, name):
        def do_rpc(*args, **kwargs):
            # Send request to the server
            try:
                self._connection.send(json.dumps((name, args, kwargs)))
                result = json.loads(self._connection.recv())
                return result
            except (EOFError, ConnectionError) as e:
                print(f"Connection error: {e}")
                return None
        return do_rpc

class Worker:
    def __init__(self, connection):
        self.proxy = RPCProxy(connection)
        self.status = 'idle'
        self.job_progress = 0

    def get_status(self):
        try:
            cpu_usage = float(get_cpu_status()['lavg_1'])
        except Exception as e:
            cpu_usage = 0.0  # Default if there's an issue getting CPU status
            print(f"Error getting CPU status: {e}")
        
        
        
        return self.status, cpu_usage, self.job_progress

    def run_job(self, job_id):
        self.status = 'busy'
        self.job_progress = 0

        print(f"Starting job {job_id}")

        try:
            pi_value = calculate_pi_leibniz(self)
            self.job_progress = 100  # Ensure progress is set to 100 upon completion
            print(f"Job {job_id} completed with result: {pi_value}")
        except Exception as e:
            print(f"Error during job {job_id}: {e}")
        finally:
            self.status = 'idle'
            # Inform the manager that the job is completed and the worker is now idle
            completion_message = ("job_completed", job_id)
            return completion_message
            


def main():
    try:
        connection = Client(('10.188.0.2', 17000), authkey=b'peekaboo')
        worker = Worker(connection)

        while True:
            try:
                # Receive command from the manager
                message = connection.recv()
                func_name, args, _ = json.loads(message)

                # Handle the received command
                if func_name == 'get_status':
                    result = worker.get_status()
                    print('Get status:', result)
                elif func_name == 'run_job':
                    result = worker.run_job(args[0])
                else:
                    result = f"Unknown function: {func_name}"
                    print(f"Received unknown function: {func_name}")

                # Send the result back to the manager
                connection.send(json.dumps(result))

            except EOFError:
                print("Connection closed by the manager")
                break
            except json.JSONDecodeError as e:
                print(f"JSON decoding error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

    except Exception as e:
        print(f"Failed to connect to the manager: {e}")

if __name__ == '__main__':
    main()