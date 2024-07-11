import socket
import time

# Kostil' to wait db while building using docker-compose

def check_port(host, port):
    while True:
        try:
            with socket.create_connection((host, port), timeout=5) as s:
                print(f"Port {port} on {host} is open")
                break  
        except (ConnectionRefusedError, TimeoutError):
            print(f"Port {port} on {host} is not available. Retrying in 5 seconds.")
            time.sleep(5) 

host = "db" 
port = 5432  

check_port(host, port)
print("Port is available. Starting the application...")