import machine  # type: ignore
from env import FREQUENCY, PORT, WIFI_PASSWORD, WIFI_SSID  # type: ignore
from microdot import Microdot, send_file  # type: ignore
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

app = Microdot()


@app.route("/")
async def root(request):
    return page("Hello"), 200, {"Content-Type": "text/html"}


@app.route("/favicon.svg")
async def favicon(request):
    return send_file("static/favicon.svg")


@app.errorhandler(404)
async def not_found(request):
    return page("404"), 404, {"Content-Type": "text/html"}


app.run(port=PORT)
