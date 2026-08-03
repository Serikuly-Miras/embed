import json  # type: ignore
import socket  # type: ignore
import ssl  # type: ignore


def _connect(host, port, timeout, ca_path):
    addr = socket.getaddrinfo(host, port)[0][-1]
    sock = socket.socket()
    sock.settimeout(timeout)
    sock.connect(addr)
    if ca_path is not None:
        with open(ca_path, "rb") as f:
            cadata = f.read()
        sock = ssl.wrap_socket(
            sock,
            server_hostname=host,
            cert_reqs=ssl.CERT_REQUIRED,
            cadata=cadata,
        )
    else:
        sock = ssl.wrap_socket(sock, server_hostname=host)
    return sock


def _dechunk(data):
    body = b""
    while data:
        size_line, _, rest = data.partition(b"\r\n")
        size = int(size_line.split(b";")[0], 16)
        if size == 0:
            break
        body += rest[:size]
        data = rest[size + 2 :]  # skip trailing \r\n after chunk data
    return body


def _read_response(sock):
    response = b""
    while True:
        chunk = sock.read(512)
        if not chunk:
            break
        response += chunk
    sock.close()

    status_line, _, rest = response.partition(b"\r\n")
    status_code = int(status_line.split(b" ")[1])
    header_block, _, resp_body = rest.partition(b"\r\n\r\n")

    headers = {}
    for line in header_block.split(b"\r\n"):
        name, _, value = line.partition(b":")
        headers[name.decode().strip().lower()] = value.decode().strip()

    if headers.get("transfer-encoding", "").lower() == "chunked":
        resp_body = _dechunk(resp_body)

    return status_code, resp_body


def post_json(
    host,
    path,
    body,
    headers=None,
    port=443,
    timeout=10,
    ca_path="static/isrg_root_x1.der",
):
    """
    Minimal HTTPS POST. Returns (status_code, response_body).

    ca_path points to a DER-encoded CA cert used to verify the server
    Pass None to skip verification.
    """
    sock = _connect(host, port, timeout, ca_path)

    request_headers = {
        "Host": host,
        "Content-Type": "application/json",
        "Content-Length": str(len(body)),
        "Connection": "close",
    }
    request_headers.update(headers or {})
    header_lines = "".join(f"{k}: {v}\r\n" for k, v in request_headers.items())

    sock.write(f"POST {path} HTTP/1.1\r\n{header_lines}\r\n".encode())
    sock.write(body)

    return _read_response(sock)


def get(host, path, headers=None, port=443, timeout=10, ca_path=None):
    """
    Minimal HTTPS GET. Returns (status_code, response_body).

    ca_path points to a DER-encoded CA cert used to verify the server.
    Defaults to None (no verification) since this is meant for quick,
    low-stakes lookups against arbitrary public APIs.
    """
    sock = _connect(host, port, timeout, ca_path)

    request_headers = {"Host": host, "Connection": "close"}
    request_headers.update(headers or {})
    header_lines = "".join(f"{k}: {v}\r\n" for k, v in request_headers.items())

    sock.write(f"GET {path} HTTP/1.1\r\n{header_lines}\r\n".encode())

    return _read_response(sock)


def get_json(host, path, **kwargs):
    status, body = get(host, path, **kwargs)
    if status != 200:
        raise ValueError(f"GET {host}{path} failed: {status}")
    return json.loads(body)
