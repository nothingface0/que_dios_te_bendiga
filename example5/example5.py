"""
Example 5
"""
import re
import sys
import socket
import argparse
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time

ADDRESS = "127.0.0.1"
PORT = 8080

FILES_TO_BUILD = {
    "index.html": {
        "template": """
<!doctype html>
<html>

<body>
    <h1>{{header}}</h1>
    <p>{{paragraph}}</p>
</body>

</html>
""",
        "params": {
            "header": "Michel needs to tighten his sk8 tracks",
            "paragraph": "It's easier to ollie that way.",
        },
    }
}


def get_formatted_header(status_code=200, status_message="OK"):
    return f"""HTTP/1.1 {status_code} {status_message}
accept-ranges: bytes
Cache-Control: private, max-age=0
date: {format_date_time(mktime(datetime.now().timetuple()))}
expires: -1
last-modified: {format_date_time(mktime(datetime.now().timetuple()))}

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
                    line = re.sub(regex, v, line)

                rendered_template += line

            return rendered_template
    except Exception as e:
        print(f"Failed to open {template_filename} ({e})!")
    return ""


def build_site(files_to_build: dict) -> None:
    for filename, config in files_to_build.items():
        print(f"Building file '{filename}'")
        with open(filename, "w+") as f:
            f.write(config["template"])

        rendered_html = render_template(filename, **config["params"])

        with open(filename, "w") as f:
            print(rendered_html)
            f.write(rendered_html)


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


parser = argparse.ArgumentParser(
    prog="example5",
    description="Program that can generate and serve HTML files",
    epilog="BOTTOM TEXT",
)

parser.add_argument("-b", "--build", action="store_true")

if __name__ == "__main__":
    args = parser.parse_args()
    if args.build:
        build_site(FILES_TO_BUILD)
        print("All files built, exiting")
        sys.exit(0)

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
                response = get_formatted_header() + load_file_contents("index.html")
                print(response)

                conn.sendall(response.encode())
                print("ok, next, please\n\n")

    print("Exiting")
