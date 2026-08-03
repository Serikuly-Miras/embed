import json  # type: ignore

import machine  # type: ignore
from env import FREQUENCY, PORT, WIFI_PASSWORD, WIFI_SSID  # type: ignore
from httpserver import HTTPServer, build_response  # type: ignore
from metrics import Metrics  # type: ignore
from pipeline import ParseError, RunError, parse_to_graph, run  # type: ignore
from wifi import connect_wifi  # type: ignore

DISPLAY_LIMIT = 10

machine.freq(FREQUENCY)
connect_wifi(WIFI_SSID, WIFI_PASSWORD)

metrics = Metrics()

with open("static/index.html", "r") as f:
    INDEX_HTML = f.read()

with open("static/favicon.svg", "rb") as f:
    FAVICON = f.read()

HOME_RESPONSE = build_response(
    "200 OK",
    "text/html",
    INDEX_HTML.replace("{title}", "Cascade").encode(),
)

NOT_FOUND_RESPONSE = build_response(
    "404 Not Found",
    "text/html",
    INDEX_HTML.replace("{title}", "404").encode(),
)

FAVICON_RESPONSE = build_response(
    "200 OK",
    "image/svg+xml",
    FAVICON,
)

app = HTTPServer(PORT)
app.not_found = lambda request: NOT_FOUND_RESPONSE


@app.route("/")
def root(request):
    return HOME_RESPONSE


@app.route("/favicon.svg")
def favicon(request):
    return FAVICON_RESPONSE


@app.route("/api/metrics")
def metrics_route(request):
    return build_response(
        "200 OK",
        "application/json",
        json.dumps(metrics.raw()).encode(),
    )


@app.route("/api/parse")
def parse_route(request):
    pipeline_src = request.json().get("pipeline", "")

    if not pipeline_src.strip():
        return build_response(
            "200 OK",
            "application/json",
            json.dumps({"nodes": [], "edges": []}).encode(),
        )

    try:
        graph = parse_to_graph(pipeline_src)
    except ParseError as e:
        return build_response(
            "400 Bad Request",
            "application/json",
            json.dumps({"error": e.message, "pos": e.pos}).encode(),
        )

    return build_response("200 OK", "application/json", json.dumps(graph).encode())


def _truncate_for_display(graph):
    """
    Truncates the number of entries in each node's output
    to DISPLAY_LIMIT for display purposes.
    """
    for node in graph["nodes"]:
        value = node.get("value")
        if isinstance(value, list) and len(value) > DISPLAY_LIMIT:
            node["value"] = value[:DISPLAY_LIMIT]
    return graph


@app.route("/api/run")
def run_route(request):
    pipeline_src = request.json().get("pipeline", "")

    if not pipeline_src.strip():
        return build_response(
            "200 OK",
            "application/json",
            json.dumps({"nodes": [], "edges": []}).encode(),
        )

    try:
        graph = run(pipeline_src)
    except ParseError as e:
        return build_response(
            "400 Bad Request",
            "application/json",
            json.dumps({"error": e.message, "pos": e.pos}).encode(),
        )
    except RunError as e:
        return build_response(
            "400 Bad Request",
            "application/json",
            json.dumps({"error": e.message, "node_id": e.node_id}).encode(),
        )

    return build_response(
        "200 OK", "application/json", json.dumps(_truncate_for_display(graph)).encode()
    )


app.serve()
