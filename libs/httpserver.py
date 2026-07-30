import json  # type: ignore
import socket  # type: ignore

MAX_HEADER_BYTES = 4096
MAX_BODY_BYTES = 16384


def build_response(status, content_type, body):
    headers = f"HTTP/1.1 {status}\r\nContent-Type: {content_type}\r\nConnection: close\r\n\r\n"
    return headers.encode() + body


class Request:
    def __init__(self, method, path, headers, body):
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body

    def json(self):
        return json.loads(self.body)


class HTTPServer:
    def __init__(self, port, led=None):
        self.port = port
        self.routes = {}
        self.led = led  # machine.Pin, blinked (active-low) while handling a request
        self.not_found = lambda request: build_response(
            "404 Not Found", "text/plain", b"Not Found"
        )

    def route(self, path):
        def register(handler):
            self.routes[path] = handler
            return handler

        return register

    def serve(self):
        addr = socket.getaddrinfo("0.0.0.0", self.port)[0][-1]
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(addr)
        server.listen(5)
        print("Listening on", addr)

        while True:
            conn, _ = server.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            try:
                self._handle(conn)
            finally:
                conn.close()

    def _read_request(self, conn):
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = conn.recv(1024)
            if not chunk:
                return None
            buf += chunk
            if len(buf) > MAX_HEADER_BYTES:
                raise ValueError("headers too large")

        head, _, rest = buf.partition(b"\r\n\r\n")
        lines = head.split(b"\r\n")
        method, path, _ = lines[0].decode().split(" ", 2)

        headers = {}
        for line in lines[1:]:
            name, _, value = line.partition(b":")
            headers[name.decode().strip().lower()] = value.decode().strip()

        content_length = int(headers.get("content-length", 0))
        if content_length > MAX_BODY_BYTES:
            raise ValueError("body too large")

        body = rest
        while len(body) < content_length:
            chunk = conn.recv(min(1024, content_length - len(body)))
            if not chunk:
                break
            body += chunk

        return Request(method, path, headers, body)

    def _handle(self, conn):
        if self.led:
            self.led.value(0)
        try:
            request = self._read_request(conn)
            if request is None:
                return

            handler = self.routes.get(request.path, self.not_found)
            conn.send(handler(request))
        finally:
            if self.led:
                self.led.value(1)
