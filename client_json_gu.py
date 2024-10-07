import json
import psutil
import threading
import time
from multiprocessing.connection import Client
from pi_calculation import calculate_pi_leibniz_chunked

class Worker:
    def __init__(self, connection):
        self._connection = connection
        self.keep_running = True  # Control flag to keep threads running

    def __getattr__(self, name):
        def do_rpc(*args, **kwargs):
            self._connection.send(json.dumps((name, args, kwargs)))
            result = json.loads(self._connection.recv())
            return result
        return do_rpc

    def listen_for_requests(self):
        """Continuously listens for requests from the server and responds."""
        try:
            while self.keep_running:
                request = json.loads(self._connection.recv())
                if request["action"] == "get_cpu_usage":
                    # Get the CPU usage
                    cpu_usage = psutil.cpu_percent(interval=1)
                    print(f"Reporting CPU usage: {cpu_usage}%")
                    self._connection.send(json.dumps({"cpu_usage": cpu_usage}))
        except EOFError:
            print("Connection closed by the server")
            self.keep_running = False

    # def calculate_pi(self):
    #     """Calculate Pi in chunks and report intermediate progress to the server."""
    #     try:
    #         n_terms = 50_000_000  # Randomly selected or preset for testing
    #         chunk_size = 5_000_000  # Adjust chunk size based on desired granularity
    #         pi_approx = 0

    #         for pi_partial in calculate_pi_leibniz_chunked(n_terms, chunk_size):
    #             pi_approx = pi_partial
    #             print(f"Intermediate Pi result: {4 * pi_approx}")
    #             self._connection.send(json.dumps({"intermediate_pi": 4 * pi_approx}))

    #         # Send final result of Pi
    #         final_result = 4 * pi_approx
    #         self._connection.send(json.dumps({"final_pi": final_result}))
    #         print(f"Final Pi result: {final_result}")

    #     except EOFError:
    #         print("Connection closed during Pi calculation")
    #         self.keep_running = False

# Connect to the server
c = Client(('localhost', 17000), authkey=b'peekaboo')
worker = Worker(c)

# CPU reporting thread
cpu_thread = threading.Thread(target=worker.listen_for_requests)
cpu_thread.daemon = True  # This will stop the thread when the program exits
cpu_thread.start()

# Run the Pi calculation in the main thread, but in chunks
# pi_thread = threading.Thread(target=worker.calculate_pi)
# pi_thread.daemon = True
# pi_thread.start()

# Keep the program running
# pi_thread.join()  # Wait for Pi calculation to complete
# worker.keep_running = False  # Stop the CPU thread when calculation is done
cpu_thread.join()

# c.close()  # Close the connection when done
