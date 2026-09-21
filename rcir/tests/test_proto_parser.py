"""
Tests for the regex-based .proto file parser.

Tests use hand-written proto content that matches real protobuf syntax —
not fabricated to pass, but written as actual valid proto3 definitions.
"""

import pytest
from rcir.graph.proto_parser import (
    parse_proto_content,
    parse_proto_files,
    proto_edges_from_parse_result,
    ProtoService,
    ProtoRPC,
    ProtoMessage,
    ProtoField,
)
from pathlib import Path


class TestParseProtoContent:
    """Test parsing individual .proto file content."""

    BASIC_SERVICE = '''
syntax = "proto3";
package hipstershop;

service ProductCatalogService {
    rpc ListProducts(Empty) returns (ListProductsResponse) {}
    rpc GetProduct(GetProductRequest) returns (Product) {}
    rpc SearchProducts(SearchProductsRequest) returns (SearchProductsResponse) {}
}

message Empty {}

message Product {
    string id = 1;
    string name = 2;
    string description = 3;
    string picture = 4;
    Money price_usd = 5;
    repeated string categories = 6;
}

message GetProductRequest {
    string id = 1;
}

message ListProductsResponse {
    repeated Product products = 1;
}

message SearchProductsRequest {
    string query = 1;
}

message SearchProductsResponse {
    repeated Product results = 1;
}

message Money {
    string currency_code = 1;
    int64 units = 2;
    int32 nanos = 3;
}
'''

    def test_extracts_service(self):
        result = parse_proto_content(self.BASIC_SERVICE, "demo.proto")
        assert len(result.services) == 1
        assert result.services[0].name == "ProductCatalogService"
        assert result.services[0].file_path == "demo.proto"

    def test_extracts_rpc_methods(self):
        result = parse_proto_content(self.BASIC_SERVICE, "demo.proto")
        service = result.services[0]
        assert len(service.methods) == 3

        method_names = {m.name for m in service.methods}
        assert method_names == {"ListProducts", "GetProduct", "SearchProducts"}

    def test_rpc_request_response_types(self):
        result = parse_proto_content(self.BASIC_SERVICE, "demo.proto")
        service = result.services[0]

        get_product = next(m for m in service.methods if m.name == "GetProduct")
        assert get_product.request_type == "GetProductRequest"
        assert get_product.response_type == "Product"

    def test_extracts_messages(self):
        result = parse_proto_content(self.BASIC_SERVICE, "demo.proto")
        msg_names = {m.name for m in result.messages}
        assert "Product" in msg_names
        assert "GetProductRequest" in msg_names
        assert "Money" in msg_names
        assert "Empty" in msg_names

    def test_extracts_message_fields(self):
        result = parse_proto_content(self.BASIC_SERVICE, "demo.proto")
        product = next(m for m in result.messages if m.name == "Product")
        field_names = {f.name for f in product.fields}
        assert "id" in field_names
        assert "name" in field_names
        assert "price_usd" in field_names
        assert "categories" in field_names

    def test_repeated_field_flag(self):
        result = parse_proto_content(self.BASIC_SERVICE, "demo.proto")
        product = next(m for m in result.messages if m.name == "Product")
        categories = next(f for f in product.fields if f.name == "categories")
        assert categories.repeated is True
        id_field = next(f for f in product.fields if f.name == "id")
        assert id_field.repeated is False

    def test_streaming_rpc(self):
        content = '''
service ChatService {
    rpc StreamMessages(stream ChatMessage) returns (stream ChatMessage) {}
}
message ChatMessage {
    string text = 1;
}
'''
        result = parse_proto_content(content)
        method = result.services[0].methods[0]
        assert method.client_streaming is True
        assert method.server_streaming is True

    def test_comments_stripped(self):
        content = '''
// This is a comment
service TestService {
    /* block comment */
    rpc DoThing(Request) returns (Response) {}
}
message Request { string id = 1; }
message Response { string result = 1; }
'''
        result = parse_proto_content(content)
        assert len(result.services) == 1
        assert result.services[0].methods[0].name == "DoThing"

    def test_empty_file(self):
        result = parse_proto_content("", "empty.proto")
        assert len(result.services) == 0
        assert len(result.messages) == 0
        assert result.files_parsed == 1

    def test_multiple_services(self):
        content = '''
service ServiceA {
    rpc MethodA(ReqA) returns (ResA) {}
}
service ServiceB {
    rpc MethodB(ReqB) returns (ResB) {}
}
message ReqA { string id = 1; }
message ResA { string result = 1; }
message ReqB { string id = 1; }
message ResB { string result = 1; }
'''
        result = parse_proto_content(content)
        assert len(result.services) == 2
        names = {s.name for s in result.services}
        assert names == {"ServiceA", "ServiceB"}


class TestProtoEdges:
    """Test edge generation from proto parse results."""

    def test_edges_from_service(self):
        content = '''
service CartService {
    rpc AddItem(AddItemRequest) returns (Empty) {}
    rpc GetCart(GetCartRequest) returns (Cart) {}
}
message AddItemRequest { string user_id = 1; }
message GetCartRequest { string user_id = 1; }
message Cart { string user_id = 1; }
message Empty {}
'''
        result = parse_proto_content(content, "cart.proto")
        edges = proto_edges_from_parse_result(result)

        # AddItem: request edge + response edge = 2
        # GetCart: request edge + response edge = 2
        # Total = 4
        assert len(edges) == 4

        # All should be static_exact
        for edge in edges:
            assert edge["resolution"] == "static_exact"
            assert edge["reason"]  # auditability: reason must be non-empty


class TestParseProtoFiles:
    """Test scanning a directory tree for .proto files."""

    def test_finds_proto_files_in_tree(self, tmp_path):
        # Create a mini repo with proto files
        proto_dir = tmp_path / "protos"
        proto_dir.mkdir()
        (proto_dir / "service.proto").write_text('''
service TestService {
    rpc DoWork(WorkRequest) returns (WorkResponse) {}
}
message WorkRequest { string id = 1; }
message WorkResponse { string result = 1; }
''')
        (proto_dir / "types.proto").write_text('''
message SharedType {
    int32 value = 1;
}
''')
        # Non-proto file should be ignored
        (tmp_path / "main.py").write_text("print('hello')")

        result = parse_proto_files(tmp_path)
        assert result.files_parsed == 2
        assert len(result.services) == 1
        assert len(result.messages) == 3  # WorkRequest, WorkResponse, SharedType
