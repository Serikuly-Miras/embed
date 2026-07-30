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
app.not_found = lambda path: build_response(
    "404 Not Found", "text/html", page("404").encode()
)


@app.route("/")
def root():
    return build_response("200 OK", "text/html", page("Hello").encode())


@app.route("/favicon.svg")
def favicon():
    with open("static/favicon.svg", "rb") as f:
        return build_response("200 OK", "image/svg+xml", f.read())


app.serve()
