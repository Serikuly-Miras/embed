import socket  # type: ignore
import ssl  # type: ignore


def post_json(
    host,
    path,
    body,
    headers=None,
    port=443,
    timeout=10,
    ca_path="static/isrg_root_x1.der",
):
    """Minimal HTTPS POST. Returns (status_code, response_body).

    ca_path points to a DER-encoded CA cert used to verify the server
    Pass None to skip verification.
    """
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

    response = b""
    while True:
        chunk = sock.read(512)
        if not chunk:
            break
        response += chunk
    sock.close()

    status_line, _, rest = response.partition(b"\r\n")
    status_code = int(status_line.split(b" ")[1])
    _, _, resp_body = rest.partition(b"\r\n\r\n")
    return status_code, resp_body
