"""
PolyEnterprise — End-to-End Medium-Scale Demonstration Application.

Executes a complete customer e-commerce order workflow across 8 feature-centric .poly modules:
1. User Authentication (01_identity_auth.poly)
2. Profile & RBAC (02_user_profile.poly)
3. Catalog & Pricing Engine (03_product_catalog.poly)
4. Cart & Checkout Engine (04_cart_checkout.poly)
5. Resilient Payment Gateway with Fail-Partial Recovery (05_payment_gateway.poly)
6. Order Fulfillment Pipeline (06_order_processor.poly)
7. Multi-Channel Notifications (07_notification_engine.poly)
8. SOC2 Compliance & Merkle Ledger Verification (08_audit_compliance.poly)
"""

import sys
import json
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from polyflow.parser import PolyParser
from polyflow.linker import PolyLinker
from polyflow.schema import PolySchemaValidator
from polyflow.runtime import PolyCellRuntime
from polyflow.merge import PolyMergeEngine
from polyflow.governance import PolyGovernanceEngine
from polyflow.guards import PolyGuardEngine

def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"))

def main():
    app_dir = Path(__file__).parent
    feature_files = sorted(list(app_dir.glob("*.poly")))

    safe_print("=========================================================================")
    safe_print("🏢 POLYENTERPRISE — END-TO-END MEDIUM-SCALE SYSTEM EXECUTION")
    safe_print(f"Directory: {app_dir}")
    safe_print(f"Loaded {len(feature_files)} Feature Modules (.poly)")
    safe_print("=========================================================================\n")

    parser = PolyParser()
    linker = PolyLinker(parser)
    runtime = PolyCellRuntime(default_timeout_ms=5000)
    merger = PolyMergeEngine()
    validator = PolySchemaValidator()
    guards = PolyGuardEngine()
    gov = PolyGovernanceEngine()

    # -------------------------------------------------------------------------
    # STEP 1: Validate Contracts & IDE Guards A-F across all 8 .poly modules
    # -------------------------------------------------------------------------
    safe_print("🔍 STAGE 1: SYSTEM-WIDE GOVERNANCE & IDE GUARDS A-F INSPECTION")
    total_violations = 0

    for ff in feature_files:
        ast = parser.parse_file(str(ff))
        violations = guards.inspect_ast(ast)
        is_gov_valid, gov_warnings = gov.verify_contract(ast.contract)

        status_str = "CLEAN ✅" if not violations else f"{len(violations)} VIOLATIONS ❌"
        safe_print(f"  • {ff.name:<30} -> {status_str}")

        if violations:
            total_violations += len(violations)
            for v in violations:
                safe_print(f"      - [Line {v.line_number}] {v.guard_name}: {v.message}")

    safe_print(f"Governance Check Result: {'PASS ✅' if total_violations == 0 else 'FAIL ❌'}\n")

    # -------------------------------------------------------------------------
    # STEP 2: Execute Complete Customer E-Commerce Purchase Workflow
    # -------------------------------------------------------------------------
    safe_print("=========================================================================")
    safe_print("🛍️ STAGE 2: EXECUTING END-TO-END CUSTOMER PURCHASE WORKFLOW")
    safe_print("=========================================================================\n")

    # Transaction State
    state = {}

    # 1. Identity & Auth
    safe_print("▶ [1/8] Executing 01_identity_auth.poly...")
    ast1 = parser.parse_file(str(app_dir / "01_identity_auth.poly"))
    res1 = runtime.execute_cell(ast1.language_blocks[0], {"email": "john.doe@enterprise.com", "password": "SuperSecretPassword123!"})
    out1 = res1.output
    state["user_id"] = out1["user_id"]
    state["email"] = out1["email"]
    state["token"] = out1["access_token"]
    state["role"] = out1["role"]
    gov.audit_execution("01_identity_auth.poly", "authenticate", {"user_id": state["user_id"]})
    safe_print(f"   Auth Status: {out1['status']} | User ID: {state['user_id']} | Role: {state['role']}")

    # 2. User Profile & RBAC
    safe_print("\n▶ [2/8] Executing 02_user_profile.poly...")
    ast2 = parser.parse_file(str(app_dir / "02_user_profile.poly"))
    res2 = runtime.execute_cell(ast2.language_blocks[0], {"user_id": state["user_id"], "name": "John Doe", "department": "Cloud Infra"})
    out2 = res2.output
    state["permissions"] = out2["permissions"]
    gov.audit_execution("02_user_profile.poly", "get_profile", {"permissions_count": len(state["permissions"])})
    safe_print(f"   Profile Status: {out2['status']} | Permissions: {state['permissions']}")

    # 3. Product Catalog & Pricing
    safe_print("\n▶ [3/8] Executing 03_product_catalog.poly (Volume Discount Calculation)...")
    ast3 = parser.parse_file(str(app_dir / "03_product_catalog.poly"))
    res3 = runtime.execute_cell(ast3.language_blocks[0], {"product_id": "prod_102", "quantity": 10})
    out3 = res3.output
    state["product_id"] = out3["product_id"]
    state["title"] = out3["title"]
    state["unit_price"] = out3["unit_price"]
    state["quantity"] = out3["quantity"]
    state["subtotal"] = out3["total_price"]
    gov.audit_execution("03_product_catalog.poly", "pricing_engine", {"product": state["title"], "total": state["subtotal"]})
    safe_print(f"   Catalog Product: {state['title']} | Qty: {state['quantity']} | Subtotal: ${state['subtotal']}")

    # 4. Cart & Checkout Engine
    safe_print("\n▶ [4/8] Executing 04_cart_checkout.poly...")
    ast4 = parser.parse_file(str(app_dir / "04_cart_checkout.poly"))
    res4 = runtime.execute_cell(ast4.language_blocks[0], {
        "user_id": state["user_id"],
        "items": [{"product_id": state["product_id"], "quantity": state["quantity"]}],
        "shipping_address": "100 Enterprise Way, Silicon Valley, CA"
    })
    out4 = res4.output
    state["cart_id"] = out4["cart_id"]
    state["grand_total"] = out4["grand_total"]
    gov.audit_execution("04_cart_checkout.poly", "validate_cart", {"cart_id": state["cart_id"], "grand_total": state["grand_total"]})
    safe_print(f"   Cart ID: {state['cart_id']} | Subtotal: ${out4['subtotal']} | Tax: ${out4['tax']} | Grand Total: ${state['grand_total']}")

    # 5. Payment Gateway (Fail-Partial Resilience Demonstration)
    safe_print("\n▶ [5/8] Executing 05_payment_gateway.poly...")
    safe_print("   ⚡ SIMULATING PRIMARY PYTHON CELL CONNECTION OUTAGE...")
    ast5 = parser.parse_file(str(app_dir / "05_payment_gateway.poly"))
    
    # Python cell fails
    py_res = runtime.execute_cell(ast5.language_blocks[0], {"cart_id": state["cart_id"], "amount": state["grand_total"], "simulate_fail": True})
    # Node cell recovers
    node_res = runtime.execute_cell(ast5.language_blocks[1], {"cart_id": state["cart_id"], "amount": state["grand_total"]})
    
    merged_payment = merger.merge([py_res, node_res], ast5.merge_strategy)
    pay_out = merged_payment["output"]
    state["payment_id"] = pay_out["payment_id"]
    state["gateway"] = pay_out["gateway"]
    gov.audit_execution("05_payment_gateway.poly", "payment_processed", {"payment_id": state["payment_id"], "gateway": state["gateway"]})
    safe_print(f"   Payment Result: {pay_out['status'].upper()} ✅")
    safe_print(f"   Winner Cell:    {merged_payment['winner']}")
    safe_print(f"   Gateway Used:   {state['gateway']}")
    if "resilience_notice" in pay_out:
        safe_print(f"   Resilience:     {pay_out['resilience_notice']}")

    # 6. Order Processor State Machine
    safe_print("\n▶ [6/8] Executing 06_order_processor.poly...")
    ast6 = parser.parse_file(str(app_dir / "06_order_processor.poly"))
    res6_py = runtime.execute_cell(ast6.language_blocks[0], {
        "user_id": state["user_id"],
        "cart_id": state["cart_id"],
        "payment_id": state["payment_id"],
        "grand_total": state["grand_total"]
    })
    res6_js = runtime.execute_cell(ast6.language_blocks[1], {})
    merged_order = merger.merge([res6_py, res6_js], ast6.merge_strategy)
    order_out = res6_py.output
    state["order_id"] = order_out["order_id"]
    state["tracking_number"] = order_out["tracking_number"]
    gov.audit_execution("06_order_processor.poly", "order_confirmed", {"order_id": state["order_id"], "tracking": state["tracking_number"]})
    safe_print(f"   Order ID:        {state['order_id']}")
    safe_print(f"   Fulfillment:     {order_out['fulfillment_status']}")
    safe_print(f"   Tracking Number: {state['tracking_number']}")

    # 7. Multi-Channel Notification Engine
    safe_print("\n▶ [7/8] Executing 07_notification_engine.poly...")
    ast7 = parser.parse_file(str(app_dir / "07_notification_engine.poly"))
    res7_email = runtime.execute_cell(ast7.language_blocks[0], {"recipient": state["email"], "subject": f"Order Confirmation {state['order_id']}"})
    res7_webhook = runtime.execute_cell(ast7.language_blocks[1], {"subject": f"Order Confirmation {state['order_id']}"})
    merged_notif = merger.merge([res7_email, res7_webhook], ast7.merge_strategy)
    gov.audit_execution("07_notification_engine.poly", "send_notifications", {"channels": ["email", "slack"]})
    safe_print("   Notifications Dispatched:")
    safe_print(f"     - Email: {res7_email.output.get('status')} to {res7_email.output.get('recipient')}")
    safe_print(f"     - Slack Webhook: {res7_webhook.output.get('status')}")

    # 8. SOC2 Audit Compliance & Merkle Ledger
    safe_print("\n▶ [8/8] Executing 08_audit_compliance.poly...")
    ast8 = parser.parse_file(str(app_dir / "08_audit_compliance.poly"))
    res8 = runtime.execute_cell(ast8.language_blocks[0], {
        "event_type": "CUSTOMER_ORDER_FULFILLED",
        "actor": state["user_id"],
        "payload_summary": f"Order {state['order_id']} Total ${state['grand_total']}"
    })
    out8 = res8.output
    gov.audit_execution("08_audit_compliance.poly", "record_soc2", {"audit_id": out8["audit_id"]})
    safe_print(f"   SOC2 Audit ID: {out8['audit_id']}")
    safe_print(f"   Leaf Hash:     {out8['merkle_leaf_hash']}")

    # -------------------------------------------------------------------------
    # STEP 3: Cryptographic Merkle Chain Verification
    # -------------------------------------------------------------------------
    safe_print("\n=========================================================================")
    safe_print("🔒 STAGE 3: CRYPTOGRAPHIC MERKLE AUDIT LEDGER CHAIN VERIFICATION")
    safe_print("=========================================================================")
    is_chain_valid, chain_err = gov.ledger.verify_chain()
    
    safe_print(f"Total Ledger Nodes Recorded: {len(gov.ledger.chain)}")
    for node in gov.ledger.chain:
        safe_print(f"  • Node #{node.index} | Root: {node.merkle_root[:24]}... | DataHash: {node.data_hash[:16]}...")

    safe_print(f"\nMerkle Ledger Verification: {'PASSED (0 ANOMALIES) ✅' if is_chain_valid else 'FAILED ❌'}\n")

    safe_print("=========================================================================")
    safe_print("🎉 POLYENTERPRISE END-TO-END DEMONSTRATION COMPLETE!")
    safe_print("=========================================================================")

if __name__ == "__main__":
    main()
