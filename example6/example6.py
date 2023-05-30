"""
Example 6
"""

import os
import re
import socket
import select
import hashlib
import random
import base64
import threading
from datetime import datetime
from time import mktime, sleep
from wsgiref.handlers import format_date_time

ADDRESS = "127.0.0.1"
PORT = 8080
PORT_WS = 8081

REASONS_TO_TIGHTEN_TRACKS = [
    "It's easier to ollie that way.",
    "To punish those bushings.",
    "Using wrenches is fun.",
]


def get_formatted_header(status_code=200, status_message="OK", **kwargs):
    return (
        f"""HTTP/1.1 {status_code} {status_message}
accept-ranges: bytes
Cache-Control: private, max-age=0
date: {format_date_time(mktime(datetime.now().timetuple()))}
expires: -1
last-modified: {format_date_time(mktime(datetime.now().timetuple()))}
"""
        + "".join([f"{k.replace('_', '-')}: {v}\n" for k, v in kwargs.items()])
        + "\n"
    )


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


# Root URL view
def get_root_response() -> str:
    return get_formatted_header() + load_file_contents("index.html")


def router(route="/") -> str:
    """
    Function which specifies routes and gets response
    from each "view"
    """

    return get_root_response()


def http_server():
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

                data = data.decode()
                # Print it
                print(f"Received data:\n{data}")
                route = data.split(" ")[1]
                print(f"Requested route '{route}")

                print("Sending contents of index.html to client")
                # Response is header + contents
                response = router(route=route)
                print(response)

                conn.sendall(response.encode())


def ws_client_key_response(sec_websocket_key: str = "") -> str:
    """
    The Sec-WebSocket-Accept header is important in that the
    server must derive it from the Sec-WebSocket-Key that the
    client sent to it. To get it, concatenate the client's
    Sec-WebSocket-Key and the string
    "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    together (it's a "magic string"), take
    the SHA-1 hash of the result, and return the base64
    encoding of that hash.
    """
    result = sec_websocket_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    result = hashlib.sha1(result.encode())
    result = base64.b64encode(result.digest())
    return result.decode()


def ws_encode(payload: str = ""):
    """
    From here:
    https://stackoverflow.com/questions/24355159/encode-data-to-send-to-a-websocket-server
    """
    data = [ord(i) for i in payload]
    length = len(payload) + 128
    Bytes = [0x81, length]
    index = 2
    masks = os.urandom(4)
    for i in range(len(masks)):
        Bytes.insert(i + index, masks[i])
    for i in range(len(data)):
        data[i] ^= masks[i % 4]
        Bytes.insert(i + index + 4, data[i])
    Bytes = bytearray(Bytes)
    return Bytes


def ws_decode(frame):
    """
    From here
    https://stackoverflow.com/questions/15740134/websocket-frame-decoding-in-python
    """
    length = frame[1] & 127

    indexFirstMask = 2
    if length == 126:
        indexFirstMask = 4
    elif length == 127:
        indexFirstMask = 10

    indexFirstDataByte = indexFirstMask + 4
    mask = frame[indexFirstMask:indexFirstDataByte]

    i = indexFirstDataByte
    j = 0
    decoded = []
    while i < len(frame):
        decoded.append(frame[i] ^ mask[j % 4])
        i += 1
        j += 1
    return "".join(chr(byte) for byte in decoded)


def ws_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((ADDRESS, PORT_WS))
        print(f"Listening on {ADDRESS}:{PORT_WS}")
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

                data = data.decode()
                # Print it
                print(f"Received data:\n{data}")

                if "Upgrade: websocket" in data:
                    m = re.search(
                        "Sec-WebSocket-Key:\s+(?P<sec_websocket_key>[\w\d\=\+\/]+)\s*",
                        data,
                    )
                    if not m:
                        raise Exception(
                            "Could not find Sec-WebSocket-Key in request header"
                        )

                    response = get_formatted_header(
                        status_code=101,
                        status_message="Switching protocols",
                        Upgrade="websocket",
                        Connection="Upgrade",
                        Sec_WebSocket_Accept=ws_client_key_response(m.group(1)),
                    )

                    conn.sendall(response.encode())
                    print("WS handshake complete")

                    # ????
                    try:
                        # Start listening to connected WS client
                        while True:
                            conn.sendall(
                                ws_encode(
                                    '{"header":"Michel needs to tighten his sk8 tracks","paragraph":"'
                                    + random.choice(REASONS_TO_TIGHTEN_TRACKS)
                                    + '"}'
                                )
                            )
                            try:
                                # From: https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
                                ready = select.select([conn], [], [], 5)
                                if ready[0]:
                                    data = conn.recv(1024)
                                    print(f"!!! received: {ws_decode(data)}")
                            except IndexError:
                                continue
                            except Exception as e:
                                print(f"!!!! Exception {repr(e)}")
                            # sleep(1)

                    except Exception as e:
                        print(f"WS error: {repr(e)}")
                        continue


if __name__ == "__main__":
    threading.Thread(target=http_server, name="http_server").start()
    threading.Thread(target=ws_server, name="ws_server").start()
    print("Exiting")
