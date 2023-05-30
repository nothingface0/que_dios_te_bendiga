"""
Example 3
"""
import socket
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time

ADDRESS = "127.0.0.1"
PORT = 8080


def get_formatted_header(status_code=200, status_message="OK"):
    return f"""HTTP/1.1 {status_code} {status_message}
accept-ranges: bytes
Cache-Control: private, max-age=0
date: {format_date_time(mktime(datetime.now().timetuple()))}
expires: -1
last-modified: {format_date_time(mktime(datetime.now().timetuple()))}

"""


def load_file_contents(filename="index.html") -> str:
    """
    Simple text file reader
    """
    try:
        with open(filename, "r+") as f:
            return f.read()
    except Exception as e:
        print(f"Failed to open {filename} ({e})!")
    return ""


if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((ADDRESS, PORT))
        print(f"Listening on {ADDRESS}:{PORT}")
        s.listen()
        # Wait for client to connect
        while True:
            conn, addr = s.accept()

            # Client connected
            with conn:
                print(f"Client connected: {addr}")
                # Get data from client
                data = conn.recv(1024)
                if not data:
                    print("No data received")
                    break
                # Print it
                print(f"Received data:\n{data.decode()}")

                print("Sending contents of index.html to client")
                # Response is header + contents
                response = get_formatted_header() + load_file_contents()
                print(response)

                conn.sendall(response.encode())
                print("ok, next, please\n\n")

    print("Exiting")
