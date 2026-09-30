"""
HTTP route and client-call detection for cross-service edge resolution (v7 §10, Tier 1).

Detects:
1. Route handlers: Flask (@app.route), FastAPI (@router.get), Django (urlpatterns)
2. HTTP client calls: requests.get/post, httpx, aiohttp with literal URL strings

Resolution:
- Literal URL string matching a known route → static_exact
- Pattern-based URL matching (e.g., "/api/users/{id}") → static_inference
- Dynamic/computed URLs → dynamic_unresolved (reported, not silently missed)

Limitations (documented, not hidden):
- Only detects decorators in AST — dynamic route registration (e.g. add_url_rule)
  is not detected and would be flagged unsupported if encountered
- URL matching is literal substring for now — no regex route parsing
- Only Python frameworks supported
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RouteHandler:
    """A detected HTTP route handler (server-side endpoint)."""
    path: str               # the URL pattern, e.g. "/api/users"
    methods: list[str]      # HTTP methods: ["GET", "POST"], etc.
    handler_name: str       # qualified name of the handler function
    file_path: str          # file where this route is defined
    framework: str          # "flask", "fastapi", "django"

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "methods": self.methods,
            "handler_name": self.handler_name,
            "file_path": self.file_path,
            "framework": self.framework,
        }


@dataclass
class HTTPClientCall:
    """A detected HTTP client call (outbound request to a service)."""
    url: str | None          # the URL string, if literal; None if dynamic
    method: str              # HTTP method: "GET", "POST", etc.
    caller_name: str         # qualified name of the calling function
    file_path: str           # file where this call is made
    library: str             # "requests", "httpx", "aiohttp"
    is_dynamic: bool = False # True if URL is computed, not a literal string

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "method": self.method,
            "caller_name": self.caller_name,
            "file_path": self.file_path,
            "library": self.library,
            "is_dynamic": self.is_dynamic,
        }


@dataclass
class HTTPParseResult:
    """Result of scanning Python files for HTTP routes and client calls."""
    routes: list[RouteHandler] = field(default_factory=list)
    client_calls: list[HTTPClientCall] = field(default_factory=list)
    files_scanned: int = 0


class _RouteVisitor(ast.NodeVisitor):
    """AST visitor that detects HTTP route decorators and client calls."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.routes: list[RouteHandler] = []
        self.client_calls: list[HTTPClientCall] = []
        self._function_stack: list[str] = []
        self._class_stack: list[str] = []

    def _current_qualified_name(self, func_name: str) -> str:
        parts = list(self._class_stack) + [func_name]
        return f"{self.file_path}::{'.' .join(parts)}"

    # --- Route handler detection ---

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        qname = self._current_qualified_name(node.name)

        # Check decorators for route patterns
        for decorator in node.decorator_list:
            route = self._check_route_decorator(decorator, qname)
            if route:
                self.routes.append(route)

        # Scan function body for HTTP client calls
        self._function_stack.append(node.name)
        self._scan_body_for_client_calls(node.body, qname)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef):
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def _check_route_decorator(
        self, decorator: ast.expr, handler_name: str
    ) -> RouteHandler | None:
        """Check if a decorator is a route registration.

        Detects patterns:
        - @app.route("/path", methods=["GET"])    # Flask
        - @router.get("/path")                     # FastAPI
        - @app.get("/path")                        # FastAPI
        """
        if isinstance(decorator, ast.Call):
            func = decorator.func

            # Flask: @app.route("/path") or @blueprint.route("/path")
            if (isinstance(func, ast.Attribute) and func.attr == "route"
                    and decorator.args):
                path = self._extract_string_arg(decorator.args[0])
                if path is not None:
                    methods = self._extract_methods_kwarg(decorator)
                    return RouteHandler(
                        path=path,
                        methods=methods or ["GET"],
                        handler_name=handler_name,
                        file_path=self.file_path,
                        framework="flask",
                    )

            # FastAPI api_route: @app.api_route("/path", methods=["GET", "POST"])
            if (isinstance(func, ast.Attribute) and func.attr == "api_route"
                    and decorator.args):
                path = self._extract_string_arg(decorator.args[0])
                if path is not None:
                    methods = self._extract_methods_kwarg(decorator)
                    return RouteHandler(
                        path=path,
                        methods=methods or ["GET"],
                        handler_name=handler_name,
                        file_path=self.file_path,
                        framework="fastapi",
                    )

            # FastAPI: @router.get("/path"), @app.post("/path"), etc.
            if isinstance(func, ast.Attribute) and func.attr in (
                "get", "post", "put", "delete", "patch", "head", "options"
            ):
                if decorator.args:
                    path = self._extract_string_arg(decorator.args[0])
                    if path is not None:
                        return RouteHandler(
                            path=path,
                            methods=[func.attr.upper()],
                            handler_name=handler_name,
                            file_path=self.file_path,
                            framework="fastapi",
                        )

        return None

    def visit_Assign(self, node: ast.Assign):
        self._check_django_urlpatterns(node)
        self.generic_visit(node)

    def _check_django_urlpatterns(self, node: ast.Assign):
        """Check for Django urlpatterns: urlpatterns = [ path('orders/', views.orders), ... ]"""
        is_urlpatterns = False
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "urlpatterns":
                is_urlpatterns = True
                break
        if not is_urlpatterns or not isinstance(node.value, (ast.List, ast.Tuple)):
            return

        for elt in node.value.elts:
            if isinstance(elt, ast.Call):
                func_name = ""
                if isinstance(elt.func, ast.Name):
                    func_name = elt.func.id
                elif isinstance(elt.func, ast.Attribute):
                    func_name = elt.func.attr

                if func_name in ("path", "re_path") and len(elt.args) >= 2:
                    path_str = self._extract_string_arg(elt.args[0])
                    if path_str is not None:
                        if func_name == "re_path":
                            path_str = path_str.lstrip("^").rstrip("$")
                        handler_name = self._resolve_expr_name(elt.args[1])
                        self.routes.append(RouteHandler(
                            path=path_str,
                            methods=["GET", "POST"],
                            handler_name=f"{self.file_path}::{handler_name}",
                            file_path=self.file_path,
                            framework="django",
                        ))

    def _resolve_expr_name(self, node: ast.expr) -> str:
        """Resolve a handler expression (e.g. views.orders, OrderView.as_view) to string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._resolve_expr_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._resolve_expr_name(node.func)
        return "view_handler"

    def _extract_string_arg(self, node: ast.expr) -> str | None:
        """Extract a literal string from an AST node."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def _extract_methods_kwarg(self, call: ast.Call) -> list[str] | None:
        """Extract methods=["GET", "POST"] from a route decorator."""
        for kw in call.keywords:
            if kw.arg == "methods" and isinstance(kw.value, ast.List):
                methods = []
                for elt in kw.value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        methods.append(elt.value.upper())
                return methods if methods else None
        return None

    # --- HTTP client call detection ---

    def _scan_body_for_client_calls(
        self, body: list[ast.stmt], caller_name: str
    ) -> None:
        """Recursively scan function body for HTTP client calls."""
        for node in ast.walk(ast.Module(body=body, type_ignores=[])):
            if isinstance(node, ast.Call):
                client_call = self._check_client_call(node, caller_name)
                if client_call:
                    self.client_calls.append(client_call)

    def _check_client_call(
        self, call: ast.Call, caller_name: str
    ) -> HTTPClientCall | None:
        """Check if a Call node is an HTTP client call.

        Detects: requests.get/post/request, httpx.get/post/request, aiohttp patterns.
        """
        func = call.func

        # requests.get("url"), requests.post("url"), httpx.get("url"), etc.
        if isinstance(func, ast.Attribute) and func.attr in (
            "get", "post", "put", "delete", "patch", "head", "options"
        ):
            obj_name = self._get_object_name(func.value)
            if obj_name in ("requests", "httpx", "self.client", "client", "session", "aiohttp"):
                library = obj_name if obj_name in ("requests", "httpx", "aiohttp") else "http_client"
                url, is_dynamic = self._extract_url_arg(call)
                return HTTPClientCall(
                    url=url,
                    method=func.attr.upper(),
                    caller_name=caller_name,
                    file_path=self.file_path,
                    library=library,
                    is_dynamic=is_dynamic,
                )

        # requests.request("GET", "url"), httpx.request("POST", "url"), etc.
        if isinstance(func, ast.Attribute) and func.attr == "request":
            obj_name = self._get_object_name(func.value)
            if obj_name in ("requests", "httpx", "self.client", "client", "session", "aiohttp"):
                if len(call.args) >= 2:
                    method_str = self._extract_string_arg(call.args[0]) or "GET"
                    # URL is 2nd argument
                    url, is_dynamic = self._extract_url_from_node(call.args[1])
                    library = obj_name if obj_name in ("requests", "httpx", "aiohttp") else "http_client"
                    return HTTPClientCall(
                        url=url,
                        method=method_str.upper(),
                        caller_name=caller_name,
                        file_path=self.file_path,
                        library=library,
                        is_dynamic=is_dynamic,
                    )

        return None

    def _get_object_name(self, node: ast.expr) -> str | None:
        """Get the name of the object a method is called on."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = self._get_object_name(node.value)
            if parent:
                return f"{parent}.{node.attr}"
        return None

    def _extract_url_arg(self, call: ast.Call) -> tuple[str | None, bool]:
        """Extract the URL from an HTTP client call."""
        arg_node = None
        if call.args:
            arg_node = call.args[0]
        else:
            for kw in call.keywords:
                if kw.arg == "url":
                    arg_node = kw.value
                    break
        return self._extract_url_from_node(arg_node)

    def _extract_url_from_node(self, arg_node: ast.expr | None) -> tuple[str | None, bool]:
        """Extract the URL string or template from an AST expression node."""
        if arg_node is None:
            return (None, True)

        # 1. Literal string constant
        if isinstance(arg_node, ast.Constant) and isinstance(arg_node.value, str):
            return (arg_node.value, False)

        # 2. f-string (ast.JoinedStr)
        if isinstance(arg_node, ast.JoinedStr):
            parts = []
            has_static = False
            for part in arg_node.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    parts.append(part.value)
                    if part.value.strip("/"):
                        has_static = True
                elif isinstance(part, ast.FormattedValue):
                    parts.append("{PARAM}")
                else:
                    parts.append("{PARAM}")
            if has_static:
                return ("".join(parts), False)
            return (None, True)

        # 3. String concatenation (ast.BinOp with ast.Add)
        if isinstance(arg_node, ast.BinOp) and isinstance(arg_node.op, ast.Add):
            template = self._extract_binop_template(arg_node)
            if template:
                return (template, False)
            return (None, True)

        return (None, True)

    def _extract_binop_template(self, node: ast.BinOp) -> str | None:
        """Extract static template from string concatenation tree."""
        left = node.left
        right = node.right

        if isinstance(left, ast.Constant) and isinstance(left.value, str):
            left_str = left.value
        elif isinstance(left, ast.BinOp) and isinstance(left.op, ast.Add):
            left_str = self._extract_binop_template(left)
        else:
            left_str = "{PARAM}"

        if isinstance(right, ast.Constant) and isinstance(right.value, str):
            right_str = right.value
        elif isinstance(right, ast.BinOp) and isinstance(right.op, ast.Add):
            right_str = self._extract_binop_template(right)
        else:
            right_str = "{PARAM}"

        combined = (left_str or "") + (right_str or "")
        if combined.replace("{PARAM}", "").strip("/"):
            return combined
        return None


def extract_http_routes(
    source: str,
    file_path: str,
    tree: ast.AST | None = None,
) -> HTTPParseResult:
    """Extract HTTP routes and client calls from Python source code or pre-parsed AST.

    Args:
        source: Python source code (if tree is None).
        file_path: Relative path of the file.
        tree: Optional pre-parsed AST tree to avoid redundant parsing.

    Returns:
        HTTPParseResult with detected routes and client calls.
    """
    result = HTTPParseResult(files_scanned=1)

    if tree is None:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return result

    visitor = _RouteVisitor(file_path)
    visitor.visit(tree)
    result.routes = visitor.routes
    result.client_calls = visitor.client_calls

    return result


def match_client_calls_to_routes(
    routes: list[RouteHandler],
    client_calls: list[HTTPClientCall],
) -> list[dict]:
    """Match HTTP client calls to route handlers by URL.

    Returns a list of edge dicts ready for the dependency graph.

    Resolution logic:
    - Literal URL exactly matches a route path → static_exact
    - Literal URL matches with path parameter substitution → static_inference
    - Dynamic URL → dynamic_unresolved (reported, not silently missed)
    """
    edges = []

    # Normalize routes for matching
    route_by_path: dict[str, list[RouteHandler]] = {}
    for route in routes:
        normalized = _normalize_route_path(route.path)
        route_by_path.setdefault(normalized, []).append(route)

    for call in client_calls:
        if call.is_dynamic or call.url is None:
            # Dynamic URL — flag as unresolved, don't silently skip
            edges.append({
                "source": call.caller_name,
                "target": "UNRESOLVED_HTTP_ENDPOINT",
                "edge_type": "calls",
                "resolution": "dynamic_unresolved",
                "reason": (
                    f"HTTP {call.method} call with dynamic/computed URL "
                    f"in {call.file_path} — cannot statically resolve target"
                ),
            })
            continue

        # Try exact match
        normalized_url = _normalize_route_path(call.url)
        matched_routes = route_by_path.get(normalized_url, [])

        if matched_routes:
            for route in matched_routes:
                res = "static_inference" if "{param}" in normalized_url else "static_exact"
                edges.append({
                    "source": call.caller_name,
                    "target": route.handler_name,
                    "edge_type": "calls",
                    "resolution": res,
                    "reason": (
                        f"HTTP {call.method} to '{call.url}' matches "
                        f"route handler {route.handler_name} at '{route.path}'"
                    ),
                })
        else:
            # Try pattern match (route has path params like /users/{id})
            matched = False
            for path, path_routes in route_by_path.items():
                if _route_pattern_matches(call.url, path):
                    for route in path_routes:
                        edges.append({
                            "source": call.caller_name,
                            "target": route.handler_name,
                            "edge_type": "calls",
                            "resolution": "static_inference",
                            "reason": (
                                f"HTTP {call.method} to '{call.url}' matches "
                                f"route pattern '{route.path}' by path-parameter inference"
                            ),
                        })
                    matched = True
                    break

            if not matched:
                # No route matches — this might be an external API call
                edges.append({
                    "source": call.caller_name,
                    "target": f"EXTERNAL_HTTP:{call.url}",
                    "edge_type": "calls",
                    "resolution": "static_inference",
                    "reason": (
                        f"HTTP {call.method} to '{call.url}' — no matching route found "
                        f"in the analyzed codebase; may be an external API call"
                    ),
                })

    return edges


def _normalize_route_path(path: str) -> str:
    """Normalize a route path for comparison.

    Strips scheme+host, trailing slashes, lowercases, replaces {param} with a placeholder.
    """
    path = path.strip()
    # Strip scheme + host/port: e.g. http://order-service:8080/orders -> /orders
    path = re.sub(r'^https?://[^/]+', '', path)
    if not path.startswith("/") and path:
        path = "/" + path
    path = path.rstrip("/").lower()
    # Replace path parameters like {id} or <id> or :id with a placeholder
    path = re.sub(r'\{[^}]+\}', '{param}', path)
    path = re.sub(r'<[^>]+>', '{param}', path)
    path = re.sub(r':(\w+)', '{param}', path)
    return path


def _route_pattern_matches(url: str, route_pattern: str) -> bool:
    """Check if a literal or parameterized URL matches a route pattern with parameters.

    e.g., "http://order-service/api/users/123" matches "/api/users/{param}"
    e.g., "http://order-service/api/users/{PARAM}" matches "/api/users/{param}"
    """
    normalized_url = _normalize_route_path(url)
    normalized_pattern = _normalize_route_path(route_pattern)

    url_parts = normalized_url.strip("/").split("/")
    pattern_parts = normalized_pattern.strip("/").split("/")

    if len(url_parts) != len(pattern_parts):
        return False

    for url_part, pattern_part in zip(url_parts, pattern_parts):
        if pattern_part == "{param}" or url_part == "{param}":
            continue  # wildcard matches anything
        if url_part != pattern_part:
            return False

    return True
