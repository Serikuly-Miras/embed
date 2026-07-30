import socket  # type: ignore


def build_response(status, content_type, body):
    headers = f"HTTP/1.1 {status}\r\nContent-Type: {content_type}\r\nConnection: close\r\n\r\n"
    return headers.encode() + body


class HTTPServer:
    def __init__(self, port):
        self.port = port
        self.routes = {}
        self.not_found = lambda path: build_response(
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

    def _handle(self, conn):
        # Small requests (a GET with a few headers) fit in one recv, avoiding
        # the extra syscalls readline()-per-header would cost.
        request = conn.recv(1024)
        if not request:
            return

        path = request.split(b" ", 2)[1].decode()
        handler = self.routes.get(path, lambda: self.not_found(path))
        conn.send(handler())
