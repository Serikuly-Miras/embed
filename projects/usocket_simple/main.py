import json  # type: ignore

import machine  # type: ignore
from env import FREQUENCY, PORT, WIFI_PASSWORD, WIFI_SSID  # type: ignore
from httpserver import HTTPServer, build_response  # type: ignore
from wifi import connect_wifi  # type: ignore

machine.freq(FREQUENCY)


def page(title):
    return f"""
<!doctype html>
<html lang="en">
  <head>
    <title>{title}</title>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body class="bg-black h-screen flex items-center justify-center">
    <h1 class="text-white font-bold text-4xl">{title}</h1>
  </body>
</html>
"""


connect_wifi(WIFI_SSID, WIFI_PASSWORD)

led = machine.Pin(8, machine.Pin.OUT)
app = HTTPServer(PORT, led=led)

# Precompute static responses once at startup instead of re-rendering and
# re-encoding on every request.
HOME_RESPONSE = build_response("200 OK", "text/html", page("Hello").encode())
NOT_FOUND_RESPONSE = build_response("404 Not Found", "text/html", page("404").encode())
with open("static/favicon.svg", "rb") as f:
    FAVICON_RESPONSE = build_response("200 OK", "image/svg+xml", f.read())

app.not_found = lambda request: NOT_FOUND_RESPONSE


@app.route("/")
def root(request):
    return HOME_RESPONSE


@app.route("/favicon.svg")
def favicon(request):
    return FAVICON_RESPONSE


@app.route("/echo")
def echo(request):
    try:
        data = request.json()
    except ValueError:
        return build_response(
            "400 Bad Request", "application/json", b'{"error":"invalid json"}'
        )
    return build_response("200 OK", "application/json", json.dumps(data).encode())


app.serve()
