"""
Tests for Polyglot Cross-Service Scanner (v7 §10).

Verifies extraction of gRPC client calls, server registrations, and HTTP routes
across Go, C#, Java, and JavaScript/TypeScript without external dependencies.
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rcir.graph.polyglot_scanner import (
    scan_source_file,
    scan_polyglot_repo,
    CrossServiceCall,
    CrossServiceEndpoint,
)


class TestGoScanning:
    """Test Go gRPC and HTTP detection."""

    GO_SOURCE = '''
package main

import (
    "context"
    "net/http"
    pb "github.com/example/demo/protos"
)

func (cs *checkoutService) PlaceOrder(ctx context.Context, req *pb.PlaceOrderRequest) error {
    cartResp, err := pb.NewCartServiceClient(cs.cartConn).GetCart(ctx, &pb.GetCartRequest{UserId: req.UserId})
    if err != nil {
        return err
    }
    return nil
}

func main() {
    pb.RegisterCheckoutServiceServer(srv, svc)
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte("ok"))
    })
}
'''

    def test_extracts_go_grpc_calls(self):
        calls, endpoints = scan_source_file(self.GO_SOURCE, "main.go")

        assert len(calls) >= 1
        call = next(c for c in calls if c.service_name == "CartService")
        assert call.method_name == "GetCart"
        assert call.call_type == "grpc"
        assert "PlaceOrder" in call.caller_symbol

    def test_extracts_go_server_registration(self):
        calls, endpoints = scan_source_file(self.GO_SOURCE, "main.go")

        assert len(endpoints) >= 1
        ep = next(e for e in endpoints if e.service_name == "CheckoutService")
        assert ep.endpoint_type == "grpc"

    def test_extracts_go_http_routes_and_calls(self):
        go_code = '''
package main
func setup() {
    r.GET("/api/v1/orders", getOrders)
    resp, _ := http.Get("http://payment-service/charge")
}
'''
        calls, endpoints = scan_source_file(go_code, "server.go")
        assert any(ep.service_name == "/api/v1/orders" and ep.endpoint_type == "http" for ep in endpoints)
        assert any("http://payment-service/charge" in c.service_name and c.call_type == "http" for c in calls)


class TestCSharpScanning:
    """Test C# gRPC client and server detection."""

    CS_SOURCE = '''
using System.Threading.Tasks;
using Hipstershop;

namespace CartService {
    public class CartServiceImpl : CartService.CartServiceBase {
        public override Task<Empty> AddItem(AddItemRequest request, ServerCallContext context) {
            return Task.FromResult(new Empty());
        }
    }

    public class ClientWrapper {
        public async Task CallEmail() {
            var client = new EmailService.EmailServiceClient(channel);
            await client.SendOrderConfirmationAsync(req);
        }
    }
}
'''

    def test_extracts_csharp_client_and_server(self):
        calls, endpoints = scan_source_file(self.CS_SOURCE, "CartService.cs")

        assert len(endpoints) >= 1
        ep = next(e for e in endpoints if e.service_name == "CartService")
        assert ep.endpoint_type == "grpc"

        assert len(calls) >= 1
        call = next(c for c in calls if c.service_name == "EmailService")
        assert call.call_type == "grpc"


class TestJavaScanning:
    """Test Java gRPC stub and server detection."""

    JAVA_SOURCE = '''
package hipstershop;

import io.grpc.stub.StreamObserver;

public class PaymentServiceImpl extends PaymentServiceGrpc.PaymentServiceImplBase {
    @Override
    public void charge(ChargeRequest req, StreamObserver<ChargeResponse> responseObserver) {
        responseObserver.onNext(ChargeResponse.newBuilder().build());
        responseObserver.onCompleted();
    }

    public void forwardNotification() {
        EmailServiceGrpc.EmailServiceBlockingStub stub = EmailServiceGrpc.newBlockingStub(channel);
    }
}
'''

    def test_extracts_java_client_and_server(self):
        calls, endpoints = scan_source_file(self.JAVA_SOURCE, "PaymentService.java")

        assert len(endpoints) >= 1
        assert endpoints[0].service_name == "PaymentService"

        assert len(calls) >= 1
        assert calls[0].service_name == "EmailService"

    def test_extracts_java_spring_routes(self):
        java_code = '''
package com.example.orders;
import org.springframework.web.bind.annotation.*;

@RestController
public class OrderController {
    @GetMapping("/orders")
    public List<Order> getOrders() { return null; }

    @PostMapping(value = "/orders/create")
    public Order createOrder(@RequestBody Order o) { return null; }
}
'''
        calls, endpoints = scan_source_file(java_code, "OrderController.java")
        assert len(endpoints) == 2
        routes = {ep.service_name: ep.method_name for ep in endpoints}
        assert routes["/orders"] == "GET"
        assert routes["/orders/create"] == "POST"


class TestJavaScriptScanning:
    """Test Node.js / TypeScript routes and gRPC client detection."""

    JS_SOURCE = '''
const express = require('express');
const app = express();

app.post('/api/checkout', (req, res) => {
    const client = new proto.CartService('localhost:50051', credentials);
    res.json({ status: 'ok' });
});

app.get('/health', (req, res) => res.send('ok'));
'''

    def test_extracts_js_routes_and_grpc(self):
        calls, endpoints = scan_source_file(self.JS_SOURCE, "server.js")

        assert len(endpoints) >= 2
        route_paths = {ep.service_name for ep in endpoints}
        assert "/api/checkout" in route_paths
        assert "/health" in route_paths

        assert len(calls) >= 1
        assert calls[0].service_name == "CartService"


class TestScanPolyglotRepo:
    """Test full directory tree scanning for polyglot files."""

    def test_scan_polyglot_repo(self, tmp_path):
        # Create Go file
        go_dir = tmp_path / "service_go"
        go_dir.mkdir()
        (go_dir / "main.go").write_text('''
package main
func CallPayment() {
    pb.NewPaymentServiceClient(conn).Charge(ctx, req)
}
''')

        # Create C# file
        cs_dir = tmp_path / "service_cs"
        cs_dir.mkdir()
        (cs_dir / "Service.cs").write_text('''
class PaymentServiceImpl : PaymentService.PaymentServiceBase {}
''')

        nodes, edges = scan_polyglot_repo(
            repo_path=tmp_path,
            known_proto_services={"PaymentService"},
        )

        assert len(nodes) >= 2
        assert len(edges) >= 2

        edge_targets = {e.target for e in edges}
        assert any("PaymentService" in t for t in edge_targets)
