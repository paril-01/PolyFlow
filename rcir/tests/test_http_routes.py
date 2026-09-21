"""
Tests for HTTP route and client-call detection.

Tests use realistic Flask and FastAPI code patterns — not fabricated to pass,
but written as code that real applications actually contain.
"""

import pytest
from rcir.graph.http_routes import (
    extract_http_routes,
    match_client_calls_to_routes,
    RouteHandler,
    HTTPClientCall,
)


class TestFlaskRouteDetection:
    """Test detection of Flask @app.route decorators."""

    def test_simple_route(self):
        source = '''
from flask import Flask
app = Flask(__name__)

@app.route("/api/users")
def get_users():
    return jsonify(users)
'''
        result = extract_http_routes(source, "app.py")
        assert len(result.routes) == 1
        route = result.routes[0]
        assert route.path == "/api/users"
        assert route.methods == ["GET"]  # default
        assert "get_users" in route.handler_name
        assert route.framework == "flask"

    def test_route_with_methods(self):
        source = '''
@app.route("/api/users", methods=["GET", "POST"])
def users_endpoint():
    pass
'''
        result = extract_http_routes(source, "app.py")
        assert len(result.routes) == 1
        assert set(result.routes[0].methods) == {"GET", "POST"}

    def test_multiple_routes(self):
        source = '''
@app.route("/api/users")
def get_users():
    pass

@app.route("/api/products")
def get_products():
    pass
'''
        result = extract_http_routes(source, "app.py")
        assert len(result.routes) == 2
        paths = {r.path for r in result.routes}
        assert paths == {"/api/users", "/api/products"}

    def test_blueprint_route(self):
        source = '''
from flask import Blueprint
bp = Blueprint("users", __name__)

@bp.route("/users/<int:user_id>")
def get_user(user_id):
    pass
'''
        result = extract_http_routes(source, "users.py")
        assert len(result.routes) == 1
        assert result.routes[0].path == "/users/<int:user_id>"


class TestFastAPIRouteDetection:
    """Test detection of FastAPI @router.get/post decorators."""

    def test_fastapi_get(self):
        source = '''
from fastapi import APIRouter
router = APIRouter()

@router.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
'''
        result = extract_http_routes(source, "items.py")
        assert len(result.routes) == 1
        route = result.routes[0]
        assert route.path == "/items/{item_id}"
        assert route.methods == ["GET"]
        assert route.framework == "fastapi"

    def test_fastapi_post(self):
        source = '''
@app.post("/items")
async def create_item(item: Item):
    pass
'''
        result = extract_http_routes(source, "items.py")
        assert len(result.routes) == 1
        assert result.routes[0].methods == ["POST"]

    def test_fastapi_multiple_methods(self):
        source = '''
@router.get("/items")
async def list_items(): pass

@router.post("/items")
async def create_item(): pass

@router.delete("/items/{item_id}")
async def delete_item(item_id: int): pass
'''
        result = extract_http_routes(source, "items.py")
        assert len(result.routes) == 3


class TestHTTPClientCallDetection:
    """Test detection of HTTP client calls (requests, httpx)."""

    def test_requests_get_literal(self):
        source = '''
import requests

def fetch_user(user_id):
    response = requests.get("http://user-service/api/users")
    return response.json()
'''
        result = extract_http_routes(source, "client.py")
        assert len(result.client_calls) == 1
        call = result.client_calls[0]
        assert call.url == "http://user-service/api/users"
        assert call.method == "GET"
        assert call.is_dynamic is False

    def test_requests_post_literal(self):
        source = '''
def create_order(data):
    response = requests.post("http://order-service/api/orders")
    return response.json()
'''
        result = extract_http_routes(source, "client.py")
        assert len(result.client_calls) == 1
        assert result.client_calls[0].method == "POST"

    def test_dynamic_url_flagged(self):
        source = '''
def fetch_product(product_id):
    url = f"http://product-service/api/products/{product_id}"
    response = requests.get(url)
    return response.json()
'''
        result = extract_http_routes(source, "client.py")
        # The requests.get(url) call should be detected as dynamic
        assert len(result.client_calls) == 1
        call = result.client_calls[0]
        assert call.is_dynamic is True
        assert call.url is None

    def test_fstring_url_flagged_dynamic(self):
        source = '''
def fetch_item(item_id):
    response = requests.get(f"http://api/items/{item_id}")
    return response.json()
'''
        result = extract_http_routes(source, "client.py")
        assert len(result.client_calls) == 1
        assert result.client_calls[0].is_dynamic is True

    def test_httpx_detected(self):
        source = '''
import httpx

def fetch_data():
    response = httpx.get("http://data-service/api/data")
    return response.json()
'''
        result = extract_http_routes(source, "client.py")
        assert len(result.client_calls) == 1
        assert result.client_calls[0].library == "httpx"


class TestRouteMatching:
    """Test matching HTTP client calls to route handlers."""

    def test_exact_match(self):
        routes = [
            RouteHandler("/api/users", ["GET"], "app.py::get_users", "app.py", "flask"),
        ]
        calls = [
            HTTPClientCall("/api/users", "GET", "client.py::fetch_users", "client.py", "requests"),
        ]
        edges = match_client_calls_to_routes(routes, calls)
        assert len(edges) == 1
        assert edges[0]["resolution"] == "static_exact"
        assert edges[0]["target"] == "app.py::get_users"

    def test_pattern_match_with_param(self):
        routes = [
            RouteHandler("/api/users/{id}", ["GET"], "app.py::get_user", "app.py", "fastapi"),
        ]
        calls = [
            HTTPClientCall("/api/users/123", "GET", "client.py::fetch", "client.py", "requests"),
        ]
        edges = match_client_calls_to_routes(routes, calls)
        assert len(edges) == 1
        assert edges[0]["resolution"] == "static_inference"

    def test_dynamic_url_unresolved(self):
        routes = [
            RouteHandler("/api/users", ["GET"], "app.py::get_users", "app.py", "flask"),
        ]
        calls = [
            HTTPClientCall(None, "GET", "client.py::fetch", "client.py", "requests", is_dynamic=True),
        ]
        edges = match_client_calls_to_routes(routes, calls)
        assert len(edges) == 1
        assert edges[0]["resolution"] == "dynamic_unresolved"
        assert edges[0]["reason"]  # auditability: reason must explain WHY

    def test_no_match_flagged_as_external(self):
        routes = [
            RouteHandler("/api/users", ["GET"], "app.py::get_users", "app.py", "flask"),
        ]
        calls = [
            HTTPClientCall("http://external-api.com/v1/data", "GET",
                          "client.py::fetch", "client.py", "requests"),
        ]
        edges = match_client_calls_to_routes(routes, calls)
        assert len(edges) == 1
        assert edges[0]["resolution"] == "static_inference"
        assert "EXTERNAL_HTTP" in edges[0]["target"]

    def test_all_edges_have_reasons(self):
        """Every edge must have a non-empty reason — v7 §1 auditability."""
        routes = [
            RouteHandler("/api/users", ["GET"], "app.py::get_users", "app.py", "flask"),
        ]
        calls = [
            HTTPClientCall("/api/users", "GET", "c.py::f1", "c.py", "requests"),
            HTTPClientCall(None, "POST", "c.py::f2", "c.py", "requests", is_dynamic=True),
            HTTPClientCall("http://external.com/x", "GET", "c.py::f3", "c.py", "requests"),
        ]
        edges = match_client_calls_to_routes(routes, calls)
        for edge in edges:
            assert edge["reason"], f"Edge missing reason: {edge}"
