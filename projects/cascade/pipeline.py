import json  # type: ignore
import time

from https import get  # type: ignore

_ticks_us = time.ticks_us
_ticks_diff = time.ticks_diff

# Blcoks


def _range(inputs, args):
    a = int(args[0]["value"])
    b = int(args[1]["value"])
    step = 1 if b >= a else -1
    return list(range(a, b + step, step))


def _sum(inputs, args):
    total = 0
    for values in inputs:
        total += sum(values)
    return [total]


def _mul(inputs, args):
    k = args[0]["value"]
    return [v * k for v in inputs[0]]


def _div(inputs, args):
    k = args[0]["value"]
    return [v / k for v in inputs[0]]


def _avg(inputs, args):
    total = 0
    count = 0
    for values in inputs:
        total += sum(values)
        count += len(values)
    return [total / count]


def _min(inputs, args):
    result = None
    for values in inputs:
        local_min = min(values)
        if result is None or local_min < result:
            result = local_min
    return [result]


def _max(inputs, args):
    result = None
    for values in inputs:
        local_max = max(values)
        if result is None or local_max > result:
            result = local_max
    return [result]


def _value(inputs, args):
    return [a["value"] for a in args]


def _weather(inputs, args):
    lat, lon = inputs[0][0], inputs[0][1]
    path = f"/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m"
    _, data = get("api.open-meteo.com", path)
    parsed = json.loads(data)
    return [parsed["current"]["temperature_2m"]]


BLOCKS = {
    "range": _range,
    "sum": _sum,
    "mul": _mul,
    "div": _div,
    "avg": _avg,
    "mean": _avg,
    "min": _min,
    "max": _max,
    "value": _value,
    "weather": _weather,
}


BLOCK_NAMES = set(BLOCKS.keys())

# Parser

TOKEN_IDENT = "IDENT"
TOKEN_NUMBER = "NUMBER"
TOKEN_LPAREN = "LPAREN"
TOKEN_RPAREN = "RPAREN"
TOKEN_LBRACKET = "LBRACKET"
TOKEN_RBRACKET = "RBRACKET"
TOKEN_COMMA = "COMMA"
TOKEN_PIPE = "PIPE"
TOKEN_EQUALS = "EQUALS"
TOKEN_NEWLINE = "NEWLINE"
TOKEN_EOF = "EOF"

_SINGLE_CHAR_TOKENS = {
    "(": TOKEN_LPAREN,
    ")": TOKEN_RPAREN,
    "[": TOKEN_LBRACKET,
    "]": TOKEN_RBRACKET,
    ",": TOKEN_COMMA,
    "|": TOKEN_PIPE,
    "=": TOKEN_EQUALS,
}


class ParseError(Exception):
    def __init__(self, message, pos):
        super().__init__(f"{message} (at {pos})")
        self.message = message
        self.pos = pos


class Token:
    def __init__(self, kind, value, pos):
        self.kind = kind
        self.value = value
        self.pos = pos

    def __repr__(self):
        return f"Token({self.kind}, {self.value!r})"


def _is_digit(c):
    return "0" <= c <= "9"


def _is_ident_start(c):
    return ("a" <= c <= "z") or ("A" <= c <= "Z") or c == "_"


def _is_ident_char(c):
    return _is_ident_start(c) or _is_digit(c)


def tokenize(src):
    tokens = []
    i = 0
    n = len(src)

    while i < n:
        c = src[i]

        if c == "\n" or c == ";":
            tokens.append(Token(TOKEN_NEWLINE, c, i))
            i += 1
            continue

        if c in " \t\r":
            i += 1
            continue

        if c == "#":
            while i < n and src[i] != "\n":
                i += 1
            continue

        if c in _SINGLE_CHAR_TOKENS:
            tokens.append(Token(_SINGLE_CHAR_TOKENS[c], c, i))
            i += 1
            continue

        if c == "-" or _is_digit(c):
            start = i
            if c == "-":
                i += 1
                if i >= n or not _is_digit(src[i]):
                    raise ParseError("expected digit after '-'", start)

            saw_dot = False
            while i < n and (_is_digit(src[i]) or src[i] == "."):
                if src[i] == ".":
                    if saw_dot:
                        raise ParseError("number has more than one '.'", start)
                    saw_dot = True
                i += 1

            text = src[start:i]
            value = float(text) if saw_dot else int(text)
            tokens.append(Token(TOKEN_NUMBER, value, start))
            continue

        if _is_ident_start(c):
            start = i
            i += 1
            while i < n and _is_ident_char(src[i]):
                i += 1
            tokens.append(Token(TOKEN_IDENT, src[start:i], start))
            continue

        raise ParseError(f"unexpected character {c!r}", i)

    tokens.append(Token(TOKEN_EOF, None, n))
    return tokens


class NumberLit:
    def __init__(self, value, is_float):
        self.value = value
        self.is_float = is_float

    def __repr__(self):
        return f"NumberLit({self.value})"


class ArrayLit:
    def __init__(self, values, is_float):
        self.values = values
        self.is_float = is_float

    def __repr__(self):
        return f"ArrayLit({self.values})"


class Ref:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Ref({self.name})"


class Call:
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __repr__(self):
        return f"Call({self.name}, {self.args})"


class Statement:
    def __init__(self, name, pipeline):
        self.name = name
        self.pipeline = pipeline

    def __repr__(self):
        return f"Statement({self.name}, {self.pipeline})"


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _peek(self):
        return self.tokens[self.pos]

    def _advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, kind):
        tok = self._peek()
        if tok.kind != kind:
            raise ParseError(f"expected {kind}, got {tok.kind}", tok.pos)
        return self._advance()

    def _skip_newlines(self):
        while self._peek().kind == TOKEN_NEWLINE:
            self._advance()

    def parse_program(self):
        statements = []
        self._skip_newlines()
        while self._peek().kind != TOKEN_EOF:
            statements.append(self._parse_statement())
            self._skip_newlines()
        return statements

    def _parse_statement(self):
        name = None
        if (
            self._peek().kind == TOKEN_IDENT
            and self.tokens[self.pos + 1].kind == TOKEN_EQUALS
        ):
            name_tok = self._advance()
            if name_tok.value in BLOCK_NAMES:
                raise ParseError(
                    f"'{name_tok.value}' is a block name, can't be used as a binding",
                    name_tok.pos,
                )
            name = name_tok.value
            self._advance()  # '='

        pipeline = [self._parse_pipeline_step()]
        while self._peek().kind == TOKEN_PIPE:
            self._advance()
            pipeline.append(self._parse_pipeline_step())

        return Statement(name, pipeline)

    def _parse_pipeline_step(self):
        ident = self._expect(TOKEN_IDENT)

        if self._peek().kind == TOKEN_LPAREN:
            return self._parse_call(ident)

        if ident.value not in BLOCK_NAMES:
            raise ParseError(f"unknown block '{ident.value}'", ident.pos)

        return Call(ident.value, [])

    def _parse_call(self, ident=None):
        ident = ident or self._expect(TOKEN_IDENT)
        self._expect(TOKEN_LPAREN)

        args = []
        if self._peek().kind != TOKEN_RPAREN:
            args.append(self._parse_arg())
            while self._peek().kind == TOKEN_COMMA:
                self._advance()
                args.append(self._parse_arg())

        self._expect(TOKEN_RPAREN)
        return Call(ident.value, args)

    def _parse_arg(self):
        tok = self._peek()

        if tok.kind == TOKEN_NUMBER:
            self._advance()
            return NumberLit(tok.value, isinstance(tok.value, float))

        if tok.kind == TOKEN_LBRACKET:
            return self._parse_array_lit()

        if tok.kind == TOKEN_IDENT:
            if self.tokens[self.pos + 1].kind == TOKEN_LPAREN:
                return self._parse_call()
            self._advance()
            if tok.value in BLOCK_NAMES:
                return Call(tok.value, [])
            return Ref(tok.value)

        raise ParseError(f"unexpected token {tok.kind} in argument", tok.pos)

    def _parse_array_lit(self):
        self._expect(TOKEN_LBRACKET)
        values = []
        is_float = False

        if self._peek().kind != TOKEN_RBRACKET:
            tok = self._expect(TOKEN_NUMBER)
            values.append(tok.value)
            is_float = is_float or isinstance(tok.value, float)
            while self._peek().kind == TOKEN_COMMA:
                self._advance()
                tok = self._expect(TOKEN_NUMBER)
                values.append(tok.value)
                is_float = is_float or isinstance(tok.value, float)

        self._expect(TOKEN_RBRACKET)
        return ArrayLit(values, is_float)


def parse(src):
    return Parser(tokenize(src)).parse_program()


def to_graph(statements):
    """
    Flatten parsed statements into a {"nodes": [...], "edges": [...]} graph.
    """

    nodes = []
    edges = []
    bindings = {}
    counter = [0]

    def new_id():
        counter[0] += 1
        return f"n{counter[0]}"

    def add_edge(source, target):
        edges.append({"id": f"e{source}-{target}", "source": source, "target": target})

    def emit_arg_value(arg):
        if isinstance(arg, NumberLit):
            return {"kind": "number", "value": arg.value, "is_float": arg.is_float}
        if isinstance(arg, ArrayLit):
            return {"kind": "array", "value": arg.values, "is_float": arg.is_float}
        raise ParseError("expected a literal argument", 0)

    def emit_call(call, piped_from):
        node_id = new_id()
        static_args = []

        for arg in call.args:
            if isinstance(arg, Ref):
                if arg.name not in bindings:
                    raise ParseError(f"unknown reference '{arg.name}'", 0)
                add_edge(bindings[arg.name], node_id)
            elif isinstance(arg, Call):
                inner_id = emit_call(arg, piped_from=None)
                add_edge(inner_id, node_id)
            else:
                static_args.append(emit_arg_value(arg))

        nodes.append(
            {
                "id": node_id,
                "name": call.name,
                "args": static_args,
            }
        )

        if piped_from is not None:
            add_edge(piped_from, node_id)

        return node_id

    for stmt in statements:
        prev_id = None
        for call in stmt.pipeline:
            prev_id = emit_call(call, piped_from=prev_id)

        if stmt.name is not None:
            bindings[stmt.name] = prev_id

    return {"nodes": nodes, "edges": edges}


def layout(graph, x_gap=286, y_gap=110):
    """
    Assigns x/y positions to nodes: x by topological depth (longest
    path from a source node), y by order within that depth column.
    """

    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    incoming = {node_id: [] for node_id in nodes_by_id}
    outgoing = {node_id: [] for node_id in nodes_by_id}

    for edge in graph["edges"]:
        outgoing[edge["source"]].append(edge["target"])
        incoming[edge["target"]].append(edge["source"])

    depth = {}

    def compute_depth(node_id, visiting):
        if node_id in depth:
            return depth[node_id]
        if node_id in visiting:
            raise ParseError("cycle detected in pipeline graph", 0)
        visiting.add(node_id)

        sources = incoming[node_id]
        d = 0 if not sources else 1 + max(compute_depth(s, visiting) for s in sources)
        depth[node_id] = d
        visiting.discard(node_id)
        return d

    for node_id in nodes_by_id:
        compute_depth(node_id, set())

    columns = {}
    for node in graph["nodes"]:
        d = depth[node["id"]]
        columns.setdefault(d, []).append(node["id"])

    for d, node_ids in columns.items():
        for row, node_id in enumerate(node_ids):
            nodes_by_id[node_id]["position"] = {
                "x": d * x_gap,
                "y": row * y_gap,
            }

    return graph


def parse_to_graph(src):
    return layout(to_graph(parse(src)))


class RunError(Exception):
    def __init__(self, message, node_id):
        super().__init__(message)
        self.message = message
        self.node_id = node_id


def execute(graph):
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    incoming = {node_id: [] for node_id in nodes_by_id}
    for edge in graph["edges"]:
        incoming[edge["target"]].append(edge["source"])

    order = sorted(
        nodes_by_id.keys(),
        key=lambda nid: (
            nodes_by_id[nid]["position"]["x"],
            nodes_by_id[nid]["position"]["y"],
        ),
    )

    values = {}
    durations = {}

    for node_id in order:
        node = nodes_by_id[node_id]
        block = BLOCKS.get(node["name"])
        if block is None:
            raise RunError(f"unknown block '{node['name']}'", node_id)

        inputs = [values[src] for src in incoming[node_id]]

        start = _ticks_us()
        try:
            values[node_id] = block(inputs, node["args"])
        except Exception as e:  # noqa: BLE001
            raise RunError(f"'{node['name']}' failed: {e}", node_id)
        durations[node_id] = _ticks_diff(_ticks_us(), start)

    return values, durations


def run(src):
    graph = parse_to_graph(src)
    values, durations = execute(graph)

    for node in graph["nodes"]:
        node["value"] = values[node["id"]]
        node["duration_us"] = durations[node["id"]]

    return graph
