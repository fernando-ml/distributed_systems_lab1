import json
from multiprocessing.connection import Client
import time
import threading
import psutil
import mnist_script  # Ensure this script is in the same directory or properly referenced

class RPCProxy:
    """
    A proxy class to handle RPC calls to the manager.
    """
    def __init__(self, connection):
        self._connection = connection

    def __getattr__(self, name):
        """
        Dynamically handle method calls and send them as RPC commands.
        """
        def do_rpc(*args, **kwargs):
            self._connection.send(json.dumps((name, args, kwargs)))
            response = json.loads(self._connection.recv())
            return response
        return do_rpc

class Worker:
    """
    Worker class that can execute jobs assigned by the manager.
    """
    def __init__(self, worker_id, proxy):
        self.worker_id = worker_id
        self.current_job = None
        self.job_progress = 0
        self.job_thread = None
        self.stop_flag = threading.Event()
        self.proxy = proxy  # RPC proxy to communicate with the manager

    def get_status(self):
        """
        Retrieve current CPU usage and job progress.
        """
        return {
            'cpu_usage': psutil.cpu_percent(interval=1),
            'job_progress': self.job_progress
        }

    def run_job(self, job_id):
        """
        Execute the assigned job. This runs in a separate thread.
        """
        self.current_job = job_id
        self.job_progress = 0
        print(f"Worker {self.worker_id}: Starting job {job_id}")

        num_epochs = 20  # Define as needed
        for epoch in range(num_epochs):
            if self.stop_flag.is_set():
                print(f"Worker {self.worker_id}: Job {job_id} stopped prematurely.")
                # Notify manager about job stoppage
                self.proxy.job_completed(self.worker_id, job_id)
                break
            mnist_script.train_model(epoch)  # Training step
            self.job_progress = ((epoch + 1) / num_epochs) * 100
            print(f"Worker {self.worker_id}: Job {job_id} progress: {self.job_progress:.2f}%")
            time.sleep(0.5)  # Simulate time taken for each epoch

        if not self.stop_flag.is_set():
            mnist_script.test_model()  # Testing after training
            result = f"Job {job_id} completed successfully."
            print(f"Worker {self.worker_id}: {result}")
            # Notify manager of job completion
            self.proxy.job_completed(self.worker_id, job_id)

        # Reset job status
        self.current_job = None
        self.job_progress = 0

    def start_job(self, job_id):
        """
        Initiate the job in a separate thread.
        """
        if self.current_job is not None:
            print(f"Worker {self.worker_id}: Already running job {self.current_job}. Cannot start job {job_id}.")
            # Send an acknowledgment with error
            self.proxy.run_job_ack(f"Failed to start job {job_id}. Worker is busy.")
            return False
        self.stop_flag.clear()
        self.job_thread = threading.Thread(target=self.run_job, args=(job_id,))
        self.job_thread.start()
        # Send acknowledgment
        self.proxy.run_job_ack("Job started successfully.")
        return True

    def stop_job(self):
        """
        Stop the currently running job.
        """
        if self.job_thread and self.job_thread.is_alive():
            self.stop_flag.set()
            self.job_thread.join()
            print(f"Worker {self.worker_id}: Job stopped.")
            # Notify manager of job stoppage
            self.proxy.job_completed(self.worker_id, self.current_job)
            self.current_job = None
            self.job_progress = 0
            # Send acknowledgment
            self.proxy.stop_job_ack("Job stopped successfully.")
            return True
        print(f"Worker {self.worker_id}: No active job to stop.")
        # Send acknowledgment
        self.proxy.stop_job_ack("No active job to stop.")
        return False

def worker_communication_thread(worker, connection):
    """
    Thread function to handle incoming RPC commands from the manager.
    """
    while True:
        try:
            data = connection.recv()
            message = json.loads(data)
            if isinstance(message, (list, tuple)) and len(message) == 3:
                func_name, args, kwargs = message
                if func_name == 'get_status':
                    status = worker.get_status()
                    # Send structured response
                    connection.send(json.dumps(("status_response", [status], {})))
                elif func_name == 'run_job':
                    job_id = args[0]
                    success = worker.start_job(job_id)
                    if not success:
                        # Send acknowledgment with error
                        connection.send(json.dumps(("run_job_response", [f"Failed to start job {job_id}. Worker is busy."], {})))
                    # No need to send acknowledgment here as start_job sends it
                elif func_name == 'stop_job':
                    success = worker.stop_job()
                    if not success:
                        # Send acknowledgment with error
                        connection.send(json.dumps(("stop_job_response", ["No active job to stop."], {})))
                    # No need to send acknowledgment here as stop_job sends it
                else:
                    # Unknown function
                    connection.send(json.dumps(("error", [f"Unknown function: {func_name}"], {})))
            else:
                # Handle unexpected message formats gracefully
                print(f"Invalid message format received: {message}")
                connection.send(json.dumps(("error", ["Invalid message format"], {})))
        except EOFError:
            print("Connection closed by manager.")
            break
        except Exception as e:
            print(f"Error in communication thread: {e}")
            connection.send(json.dumps(("error", [str(e)], {})))

def main():
    """
    Main function to initialize the worker and handle communication.
    """
    # Assign a unique worker ID (you might want to make this more robust)
    worker_id = f"worker_{int(time.time())}"
    print(f"Initializing {worker_id}...")

    # Connect to the manager
    manager_ip = '0.0.0.0'  # Replace with the actual manager IP
    manager_port = 17000
    auth_key = b'peekaboo'

    try:
        connection = Client((manager_ip, manager_port), authkey=auth_key)
        print(f"Connected to manager at {manager_ip}:{manager_port}")
    except Exception as e:
        print(f"Failed to connect to manager: {e}")
        return

    proxy = RPCProxy(connection)

    # Register and connect with the manager
    try:
        registration_response = proxy.register_and_connect(worker_id, address=('0.0.0.0', 18000))  # Adjust address as needed
        # Send structured acknowledgment
        connection.send(json.dumps(("ack", [registration_response], {})))
        print(registration_response)
    except Exception as e:
        print(f"Registration failed: {e}")
        return

    # Initialize the Worker instance
    worker = Worker(worker_id, proxy)

    # Start the communication thread
    communication_thread = threading.Thread(target=worker_communication_thread, args=(worker, connection))
    communication_thread.daemon = True  # Daemonize thread to exit when main thread does
    communication_thread.start()

    print(f"{worker_id} is now idle and waiting for job assignments.")

    # Keep the main thread alive to allow background threads to operate
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Worker shutting down gracefully.")
        if worker.current_job is not None:
            worker.stop_job()
        connection.close()

if __name__ == '__main__':
    main()