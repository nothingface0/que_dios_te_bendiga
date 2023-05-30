"""
Example 4
"""
import re
import socket
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time

ADDRESS = "127.0.0.1"
PORT = 8080


def get_formatted_header(status_code=200, status_message="OK", content_type: str = ""):
    return f"""HTTP/1.1 {status_code} {status_message}
accept-ranges: bytes
Cache-Control: private, max-age=0
date: {format_date_time(mktime(datetime.now().timetuple()))}
expires: -1
last-modified: {format_date_time(mktime(datetime.now().timetuple()))}
{"content-type: "+content_type if content_type else ""}

"""


def render_template(template_filename="index.html", **kwargs) -> str:
    """
    Given arguments, replace them in an HTML template
    """

    try:
        with open(template_filename, "r+") as f:
            rendered_template = ""
            template = f.readlines()
            for line in template:
                if not "{" in line:
                    rendered_template += line
                    continue
                # kwargs contain the template var name (k)
                # and value (v) to be replaced with
                for k, v in kwargs.items():
                    if not k in line:
                        continue
                    regex = "\{\{\s*(?P<" + k + ">\w+)\s*\}\}"
                    m = re.search(regex, line)
                    line = re.sub(regex, v, line)

                rendered_template += line
                if m:
                    print(k, m.group(0))

            return rendered_template
    except Exception as e:
        print(f"Failed to open {template_filename} ({e})!")
    return ""


# API view
def get_api_response() -> str:
    return (
        get_formatted_header(content_type="application/json")
        + '{"paragraph": "It\'s easier to ollie that way." }'
    )


# Root URL view
def get_root_response() -> str:
    return get_formatted_header() + render_template(
        "index.html",
        header="Michel needs to tighten his sk8 tracks",
    )


def router(route="/") -> str:
    """
    Function which specifies routes and gets response
    from each "view"
    """
    if route == "/api":
        return get_api_response()
    return get_root_response()


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

                data = data.decode()
                # Print it
                print(f"Received data:\n{data}")
                route = data.split(" ")[1]
                print(f"Requested route '{route}")

                print("Sending response to client")
                # Response is header + contents
                response = router(route=route)
                print(response)

                conn.sendall(response.encode())
                print("ok, next, please\n\n")

    print("Exiting")
