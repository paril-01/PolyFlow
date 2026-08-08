"""
Enterprise Commerce Platform — Master Configuration.

Defines all services, languages, feature domains, dependency graphs,
developer personas, and scaling parameters for the Synthetic Enterprise Generator.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import random

# --- Developer Personas ------------------------------------------------------

DEVELOPERS = [
    {"name": "Alice Chen",       "email": "alice.chen@ecp.dev",       "github": "alice-chen",       "team": "platform"},
    {"name": "Bob Martinez",     "email": "bob.martinez@ecp.dev",     "github": "bob-martinez",     "team": "backend"},
    {"name": "Carol Williams",   "email": "carol.williams@ecp.dev",   "github": "carol-williams",   "team": "frontend"},
    {"name": "David Kim",        "email": "david.kim@ecp.dev",        "github": "david-kim",        "team": "backend"},
    {"name": "Elena Petrov",     "email": "elena.petrov@ecp.dev",     "github": "elena-petrov",     "team": "ml"},
    {"name": "Frank Johnson",    "email": "frank.johnson@ecp.dev",    "github": "frank-johnson",    "team": "devops"},
    {"name": "Grace Liu",        "email": "grace.liu@ecp.dev",        "github": "grace-liu",        "team": "frontend"},
    {"name": "Hassan Ali",       "email": "hassan.ali@ecp.dev",       "github": "hassan-ali",       "team": "backend"},
    {"name": "Iris Nakamura",    "email": "iris.nakamura@ecp.dev",    "github": "iris-nakamura",    "team": "platform"},
    {"name": "Jake Thompson",    "email": "jake.thompson@ecp.dev",    "github": "jake-thompson",    "team": "devops"},
    {"name": "Karen Singh",      "email": "karen.singh@ecp.dev",      "github": "karen-singh",      "team": "ml"},
    {"name": "Leo Rivera",       "email": "leo.rivera@ecp.dev",       "github": "leo-rivera",       "team": "backend"},
]

# --- Service Definitions -----------------------------------------------------

@dataclass
class ServiceDef:
    name: str
    language: str
    framework: str
    port: int
    description: str
    team: str
    depends_on: List[str] = field(default_factory=list)
    package_file: str = ""
    src_dir: str = "src"

SERVICES: List[ServiceDef] = [
    ServiceDef("frontend-react",        "typescript", "react",       3000, "Customer Portal (React 18 + TypeScript)",             "frontend",  ["gateway-go"],                                     "package.json",    "src"),
    ServiceDef("frontend-angular",      "typescript", "angular",     4200, "Admin Dashboard (Angular 17 + TypeScript)",            "frontend",  ["gateway-go"],                                     "package.json",    "src/app"),
    ServiceDef("mobile-flutter",        "dart",       "flutter",     0,    "Mobile App (Flutter + Dart)",                          "frontend",  ["gateway-go"],                                     "pubspec.yaml",    "lib"),
    ServiceDef("gateway-go",            "go",         "chi",         8080, "API Gateway (Go + Chi + GraphQL)",                     "platform",  ["auth-service-java", "order-service-go", "inventory-python", "pricing-python", "recommendation-python", "ai-service-python"], "go.mod", "cmd"),
    ServiceDef("auth-service-java",     "java",       "spring-boot", 8081, "Authentication & Authorization (Spring Boot 3)",       "backend",   ["analytics-java"],                                 "pom.xml",         "src/main/java"),
    ServiceDef("payment-service-java",  "java",       "spring-boot", 8082, "Payment Processing (Spring Boot 3 + Stripe)",          "backend",   ["notification-node", "analytics-java"],             "pom.xml",         "src/main/java"),
    ServiceDef("order-service-go",      "go",         "grpc",        8083, "Order Management (Go + gRPC)",                         "backend",   ["pricing-python", "inventory-python", "payment-service-java", "notification-node"], "go.mod", "cmd"),
    ServiceDef("inventory-python",      "python",     "fastapi",     8084, "Inventory Management (Python FastAPI)",                "backend",   ["notification-node"],                              "requirements.txt","app"),
    ServiceDef("pricing-python",        "python",     "fastapi",     8085, "Dynamic Pricing Engine (Python FastAPI + ML)",          "ml",        ["analytics-java"],                                 "requirements.txt","app"),
    ServiceDef("recommendation-python", "python",     "fastapi",     8086, "Recommendation Engine (Python + scikit-learn)",         "ml",        ["ai-service-python", "analytics-java"],            "requirements.txt","app"),
    ServiceDef("notification-node",     "javascript", "express",     8087, "Notification Service (Node.js + Express + Bull)",       "platform",  [],                                                 "package.json",    "src"),
    ServiceDef("analytics-java",        "java",       "spring-boot", 8088, "Analytics & Reporting (Spring Boot + Kafka)",           "backend",   [],                                                 "pom.xml",         "src/main/java"),
    ServiceDef("ai-service-python",     "python",     "fastapi",     8089, "AI/NLP Service (Python + Transformers + FAISS)",        "ml",        [],                                                 "requirements.txt","app"),
]

SHARED_MODULES = [
    {"name": "shared-proto",  "description": "gRPC Protobuf Definitions",          "type": "proto"},
    {"name": "shared-schema", "description": "SQL Migrations + GraphQL SDL",       "type": "schema"},
    {"name": "terraform",     "description": "Infrastructure as Code (Terraform)", "type": "infra"},
    {"name": "kubernetes",    "description": "Kubernetes Manifests & Helm Charts", "type": "k8s"},
    {"name": "monitoring",    "description": "Prometheus Rules + Grafana Dashboards", "type": "monitoring"},
    {"name": "docs",          "description": "Architecture Docs, ADRs, RFCs",     "type": "docs"},
    {"name": "scripts",       "description": "Deployment & Utility Scripts",       "type": "scripts"},
    {"name": ".github",       "description": "CI/CD Workflows",                    "type": "cicd"},
    {"name": "test-suite",    "description": "Integration & E2E Tests",            "type": "test"},
    {"name": "benchmark",     "description": "Performance Benchmark Harness",      "type": "benchmark"},
]

# --- Feature Domain Definitions ----------------------------------------------

@dataclass
class FeatureDomain:
    name: str
    service: str          # primary service
    language: str
    features: List[str]   # feature IDs
    poly_prefix: str      # prefix for .poly file naming

FEATURE_DOMAINS: List[FeatureDomain] = [
    FeatureDomain("authentication", "auth-service-java", "java", [
        "jwt_token_issue", "jwt_token_verify", "jwt_token_refresh", "oauth2_pkce_flow",
        "oauth2_callback", "oauth2_token_exchange", "mfa_totp_setup", "mfa_totp_verify",
        "mfa_sms_challenge", "password_hash", "password_reset_request", "password_reset_confirm",
        "rbac_role_create", "rbac_role_assign", "rbac_permission_check", "rbac_policy_evaluate",
        "session_create", "session_validate", "session_revoke", "api_key_generate",
        "api_key_rotate", "api_key_revoke", "device_trust_register", "device_trust_verify",
        "audit_login_success", "audit_login_failure", "audit_permission_denied",
        "sso_saml_init", "sso_saml_callback", "account_lockout",
    ], "auth"),

    FeatureDomain("orders", "order-service-go", "go", [
        "order_create", "order_cancel", "order_return_request", "order_return_approve",
        "order_exchange", "order_split", "order_merge", "order_draft_create",
        "order_draft_submit", "order_bulk_create", "order_bulk_cancel",
        "order_scheduled_create", "order_scheduled_process", "order_status_update",
        "order_status_history", "order_notes_add", "order_priority_set",
        "order_shipping_calculate", "order_shipping_track", "order_shipping_update",
        "order_tax_calculate", "order_discount_apply", "order_coupon_validate",
        "order_subtotal_compute", "order_total_compute", "order_receipt_generate",
        "order_invoice_create", "order_fulfillment_start", "order_fulfillment_complete",
        "order_partial_fulfill", "order_backorder_create", "order_backorder_notify",
        "order_hold_place", "order_hold_release", "order_archive",
        "order_export_csv", "order_export_pdf", "order_search",
        "order_filter_status", "order_filter_date",
    ], "orders"),

    FeatureDomain("inventory", "inventory-python", "python", [
        "warehouse_sync", "warehouse_create", "warehouse_update", "warehouse_deactivate",
        "stock_level_get", "stock_level_update", "stock_low_alert", "stock_out_alert",
        "demand_forecast_daily", "demand_forecast_weekly", "demand_forecast_seasonal",
        "supplier_create", "supplier_update", "supplier_deactivate", "supplier_order_create",
        "restock_auto_trigger", "restock_manual_request", "restock_approval",
        "reservation_create", "reservation_release", "reservation_expire",
        "batch_tracking_create", "batch_tracking_update", "batch_expiry_check",
        "sku_generate", "sku_lookup", "sku_merge",
        "inventory_audit_start", "inventory_audit_count", "inventory_audit_reconcile",
        "location_transfer", "location_bin_assign", "location_zone_manage",
        "inventory_report_daily", "inventory_report_valuation", "inventory_snapshot",
        "dead_stock_identify", "dead_stock_markdown", "slow_mover_flag",
        "inventory_import_csv",
    ], "inventory"),

    FeatureDomain("payments", "payment-service-java", "java", [
        "stripe_charge_create", "stripe_charge_capture", "stripe_charge_refund",
        "stripe_customer_create", "stripe_payment_method_attach", "stripe_webhook_handle",
        "razorpay_order_create", "razorpay_payment_verify", "razorpay_refund",
        "paypal_order_create", "paypal_capture", "paypal_refund",
        "refund_full", "refund_partial", "refund_policy_check",
        "invoice_create", "invoice_send", "invoice_mark_paid", "invoice_void",
        "settlement_daily", "settlement_weekly", "settlement_reconcile",
        "recurring_subscription_create", "recurring_subscription_cancel", "recurring_charge",
        "escrow_hold", "escrow_release", "escrow_dispute",
        "chargeback_receive", "chargeback_respond", "chargeback_resolve",
        "payment_method_validate", "payment_method_tokenize",
        "currency_convert", "currency_rate_fetch",
        "payout_vendor_create", "payout_vendor_process", "payout_vendor_reconcile",
        "payment_report_daily", "payment_report_monthly",
        "fraud_score_compute", "fraud_rule_evaluate", "fraud_block",
        "payment_retry", "payment_timeout_handle",
    ], "payments"),

    FeatureDomain("pricing", "pricing-python", "python", [
        "price_base_set", "price_dynamic_compute", "price_surge_detect",
        "coupon_create", "coupon_validate", "coupon_apply", "coupon_expire",
        "tax_rate_lookup", "tax_calculate", "tax_exempt_check",
        "regional_price_set", "regional_price_convert", "regional_currency_detect",
        "flash_sale_create", "flash_sale_activate", "flash_sale_deactivate",
        "bundle_price_compute", "bundle_discount_apply",
        "tier_price_compute", "volume_discount_compute",
        "ab_price_test_create", "ab_price_test_evaluate", "ab_price_test_conclude",
        "margin_calculate", "margin_alert_low",
        "competitor_price_track", "competitor_price_match",
        "price_history_record", "price_history_query",
        "price_rule_create", "price_rule_evaluate", "price_rule_priority",
        "wholesale_price_compute", "clearance_price_compute",
        "price_override_manual",
    ], "pricing"),

    FeatureDomain("recommendations", "recommendation-python", "python", [
        "collab_filter_train", "collab_filter_predict", "collab_filter_retrain",
        "content_based_train", "content_based_predict",
        "trending_compute_hourly", "trending_compute_daily",
        "recently_viewed_record", "recently_viewed_fetch",
        "similar_products_compute", "similar_products_fetch",
        "embedding_generate", "embedding_index_build", "embedding_search",
        "personalization_profile_build", "personalization_score",
        "cross_sell_compute", "upsell_compute",
        "seasonal_recommend", "new_arrival_boost",
        "popularity_score_compute", "popularity_decay_apply",
        "diversity_inject", "novelty_score",
        "ab_recommend_test", "ab_recommend_evaluate",
        "feedback_implicit_record", "feedback_explicit_record",
        "cold_start_handle", "cold_start_fallback",
        "recommendation_cache_warm", "recommendation_cache_invalidate",
        "recommendation_explain", "recommendation_filter_apply",
        "recommendation_batch_compute", "recommendation_realtime_score",
        "recommendation_model_version", "recommendation_model_rollback",
        "recommendation_quality_metric", "recommendation_coverage_report",
    ], "recommendations"),

    FeatureDomain("notifications", "notification-node", "javascript", [
        "email_send", "email_template_render", "email_batch_send",
        "sms_send", "sms_template_render", "sms_delivery_status",
        "push_send_ios", "push_send_android", "push_send_web",
        "whatsapp_send", "whatsapp_template", "whatsapp_status",
        "slack_send", "slack_channel_notify", "slack_thread_reply",
        "webhook_register", "webhook_fire", "webhook_retry",
        "in_app_notification_create", "in_app_notification_read", "in_app_notification_dismiss",
        "digest_daily_compile", "digest_weekly_compile", "digest_send",
        "template_create", "template_update", "template_preview",
        "delivery_track", "delivery_retry", "delivery_bounce_handle",
        "preference_get", "preference_update", "preference_unsubscribe",
        "rate_limit_check", "notification_queue_process",
        "notification_log_store",
    ], "notifications"),

    FeatureDomain("analytics", "analytics-java", "java", [
        "revenue_dashboard_compute", "revenue_by_product", "revenue_by_region",
        "funnel_define", "funnel_compute", "funnel_compare",
        "cohort_define", "cohort_compute", "cohort_retention",
        "realtime_metric_ingest", "realtime_metric_aggregate", "realtime_metric_alert",
        "event_track", "event_batch_ingest", "event_schema_validate",
        "ab_test_create", "ab_test_assign", "ab_test_evaluate", "ab_test_conclude",
        "segment_define", "segment_compute", "segment_export",
        "report_schedule", "report_generate", "report_distribute",
        "attribution_model", "attribution_compute",
        "churn_predict", "ltv_compute",
        "dashboard_create", "dashboard_widget_add",
    ], "analytics"),

    FeatureDomain("ai_features", "ai-service-python", "python", [
        "semantic_search_index", "semantic_search_query", "semantic_search_rerank",
        "review_summarize", "review_sentiment_analyze", "review_keyword_extract",
        "product_tag_auto", "product_tag_suggest", "product_categorize",
        "fraud_detect_transaction", "fraud_detect_account", "fraud_model_retrain",
        "image_classify", "image_similarity", "image_generate_thumbnail",
        "chatbot_intent_classify", "chatbot_response_generate", "chatbot_context_manage",
        "text_translate", "text_language_detect",
        "price_predict", "demand_predict",
        "anomaly_detect_traffic", "anomaly_detect_revenue",
        "recommendation_neural", "recommendation_graph",
        "content_moderate_text", "content_moderate_image",
        "entity_extract", "relation_extract",
        "embedding_text_generate", "embedding_image_generate",
        "model_serve_inference", "model_ab_test", "model_version_manage",
    ], "ai"),

    FeatureDomain("admin", "frontend-angular", "typescript", [
        "user_list", "user_create", "user_update", "user_deactivate", "user_search",
        "feature_flag_create", "feature_flag_toggle", "feature_flag_segment",
        "permission_matrix_view", "permission_matrix_edit",
        "audit_log_view", "audit_log_filter", "audit_log_export",
        "content_moderate_queue", "content_moderate_action", "content_moderate_appeal",
        "system_health_dashboard", "system_health_service_status", "system_health_alerts",
        "config_manage", "config_history", "config_rollback",
        "api_key_admin_list", "api_key_admin_revoke",
        "report_admin_list", "report_admin_schedule",
        "notification_admin_broadcast", "notification_admin_template",
        "integration_manage", "integration_test", "integration_log",
        "backup_trigger", "backup_schedule", "backup_restore",
        "migration_run", "migration_rollback", "migration_status",
        "cache_flush", "cache_stats", "cache_warm",
    ], "admin"),

    FeatureDomain("frontend_customer", "frontend-react", "typescript", [
        "product_list_page", "product_detail_page", "product_image_gallery",
        "cart_add_item", "cart_remove_item", "cart_update_quantity", "cart_summary",
        "checkout_shipping", "checkout_payment", "checkout_review", "checkout_confirm",
        "search_autocomplete", "search_results", "search_filter_apply",
        "filter_category", "filter_price_range", "filter_brand", "filter_rating",
        "review_list", "review_create", "review_helpful_vote",
        "wishlist_add", "wishlist_remove", "wishlist_share",
        "order_history_list", "order_history_detail", "order_tracking_view",
        "account_profile_edit", "account_address_manage", "account_payment_methods",
        "notification_center", "notification_preferences",
        "recommendation_carousel", "recently_viewed_widget",
        "comparison_add", "comparison_view",
        "loyalty_points_view", "loyalty_redeem",
        "gift_card_purchase", "gift_card_redeem",
        "subscription_manage", "newsletter_signup",
        "accessibility_toggle", "theme_toggle",
        "breadcrumb_nav", "mega_menu", "footer_links",
        "mobile_responsive_layout", "infinite_scroll",
        "lazy_load_images", "skeleton_loader",
    ], "frontend"),

    FeatureDomain("infrastructure", "terraform", "hcl", [
        "vpc_create", "subnet_configure", "security_group_define",
        "ecs_cluster_create", "ecs_service_deploy", "ecs_task_definition",
        "rds_provision", "rds_replica_create", "rds_backup_configure",
        "elasticache_provision", "elasticache_cluster",
        "s3_bucket_create", "s3_lifecycle_policy", "s3_cors_configure",
        "cloudfront_distribution", "route53_record",
        "iam_role_create", "iam_policy_attach", "iam_user_create",
        "secrets_manager_store", "secrets_manager_rotate",
        "k8s_namespace_create", "k8s_deployment", "k8s_service", "k8s_ingress",
        "helm_chart_create", "helm_release_deploy",
        "docker_build", "docker_push", "docker_compose_dev",
        "prometheus_rule_create", "prometheus_alert",
        "grafana_dashboard", "grafana_datasource",
        "load_balancer_configure", "auto_scaling_policy",
        "network_policy_define", "pod_disruption_budget",
        "disaster_recovery_plan", "chaos_engineering_test",
    ], "infra"),
]

# --- Cross-Language Call Chains -----------------------------------------------

CALL_CHAINS = [
    {
        "name": "customer_purchase_flow",
        "description": "Customer adds items to cart, checks out, payment processed, notifications sent",
        "steps": [
            {"service": "frontend-react",        "language": "typescript", "action": "checkout_confirm"},
            {"service": "gateway-go",            "language": "go",         "action": "route_order_create"},
            {"service": "auth-service-java",     "language": "java",       "action": "jwt_token_verify"},
            {"service": "order-service-go",      "language": "go",         "action": "order_create"},
            {"service": "pricing-python",        "language": "python",     "action": "price_dynamic_compute"},
            {"service": "inventory-python",      "language": "python",     "action": "reservation_create"},
            {"service": "payment-service-java",  "language": "java",       "action": "stripe_charge_create"},
            {"service": "notification-node",     "language": "javascript", "action": "email_send"},
            {"service": "analytics-java",        "language": "java",       "action": "event_track"},
        ]
    },
    {
        "name": "admin_product_update",
        "description": "Admin updates product in dashboard, triggers inventory sync and price recalculation",
        "steps": [
            {"service": "frontend-angular",      "language": "typescript", "action": "config_manage"},
            {"service": "gateway-go",            "language": "go",         "action": "route_inventory_update"},
            {"service": "inventory-python",      "language": "python",     "action": "stock_level_update"},
            {"service": "pricing-python",        "language": "python",     "action": "price_dynamic_compute"},
            {"service": "recommendation-python", "language": "python",     "action": "collab_filter_retrain"},
            {"service": "analytics-java",        "language": "java",       "action": "event_track"},
            {"service": "notification-node",     "language": "javascript", "action": "slack_channel_notify"},
        ]
    },
    {
        "name": "ai_search_flow",
        "description": "Customer searches for a product using natural language, AI processes query",
        "steps": [
            {"service": "frontend-react",        "language": "typescript", "action": "search_autocomplete"},
            {"service": "gateway-go",            "language": "go",         "action": "route_search"},
            {"service": "ai-service-python",     "language": "python",     "action": "semantic_search_query"},
            {"service": "recommendation-python", "language": "python",     "action": "similar_products_fetch"},
            {"service": "pricing-python",        "language": "python",     "action": "price_base_set"},
            {"service": "analytics-java",        "language": "java",       "action": "event_track"},
        ]
    },
    {
        "name": "order_return_flow",
        "description": "Customer initiates a return, inventory restocked, refund processed",
        "steps": [
            {"service": "frontend-react",        "language": "typescript", "action": "order_history_detail"},
            {"service": "gateway-go",            "language": "go",         "action": "route_order_return"},
            {"service": "order-service-go",      "language": "go",         "action": "order_return_request"},
            {"service": "inventory-python",      "language": "python",     "action": "reservation_release"},
            {"service": "payment-service-java",  "language": "java",       "action": "refund_full"},
            {"service": "notification-node",     "language": "javascript", "action": "email_send"},
            {"service": "analytics-java",        "language": "java",       "action": "event_track"},
        ]
    },
    {
        "name": "fraud_detection_flow",
        "description": "Payment triggers AI fraud scoring, blocks suspicious transactions",
        "steps": [
            {"service": "payment-service-java",  "language": "java",       "action": "fraud_score_compute"},
            {"service": "ai-service-python",     "language": "python",     "action": "fraud_detect_transaction"},
            {"service": "auth-service-java",     "language": "java",       "action": "audit_login_failure"},
            {"service": "notification-node",     "language": "javascript", "action": "slack_channel_notify"},
            {"service": "analytics-java",        "language": "java",       "action": "realtime_metric_alert"},
        ]
    },
]

# --- Scaling Configuration ---------------------------------------------------

@dataclass
class ScaleConfig:
    name: str
    feature_multiplier: float    # 1.0 = all features, 0.5 = half
    files_per_feature: int       # avg files generated per feature
    tests_per_feature: int       # avg test cases per feature
    functions_per_file: int      # avg functions per generated file
    bug_count: int
    debt_items: int
    commit_count: int
    pr_count: int
    issue_count: int
    adr_count: int
    developer_count: int

SCALE_CONFIGS = {
    "small":  ScaleConfig("small",  0.2,  4,  2,  5,  40,   15,  1200,  24,  60,  16,  6),
    "medium": ScaleConfig("medium", 0.6,  6,  3,  8,  120,  40,  3600,  72,  180, 48,  10),
    "large":  ScaleConfig("large",  1.0,  10, 5,  12, 200,  80,  6000,  120, 300, 80,  12),
}

# --- Bug Templates -----------------------------------------------------------

BUG_TEMPLATES = {
    "python": [
        {"type": "memory_leak",       "code": "# BUG: growing list never cleared\n_cache = []\ndef process(item):\n    _cache.append(item)\n    return item"},
        {"type": "sql_injection",     "code": '# BUG: string concatenation in SQL\ndef get_user(name):\n    query = f"SELECT * FROM users WHERE name = \'{name}\'"\n    return db.execute(query)'},
        {"type": "missing_null_check","code": "# BUG: no null check\ndef get_price(product):\n    return product['pricing']['base_price'] * 1.1"},
        {"type": "circular_import",   "code": "# BUG: circular import\nfrom . import order_service\ndef process():\n    return order_service.get_orders()"},
        {"type": "race_condition",    "code": "# BUG: shared mutable state without lock\ncounter = 0\ndef increment():\n    global counter\n    temp = counter\n    counter = temp + 1"},
        {"type": "resource_leak",     "code": "# BUG: file handle never closed\ndef read_config():\n    f = open('config.yml')\n    return f.read()"},
        {"type": "infinite_recursion","code": "# BUG: no base case\ndef flatten(lst):\n    result = []\n    for item in lst:\n        result.extend(flatten(item))\n    return result"},
    ],
    "java": [
        {"type": "memory_leak",       "code": "// BUG: static list grows unbounded\nprivate static final List<Object> cache = new ArrayList<>();\npublic void process(Object item) { cache.add(item); }"},
        {"type": "sql_injection",     "code": '// BUG: string concatenation in SQL\npublic User findUser(String name) {\n    return jdbc.query("SELECT * FROM users WHERE name = \'" + name + "\'");\n}'},
        {"type": "null_pointer",      "code": "// BUG: no null check\npublic double getTotal(Order order) {\n    return order.getItems().stream().mapToDouble(Item::getPrice).sum();\n}"},
        {"type": "deadlock",          "code": "// BUG: lock ordering deadlock\nsynchronized(lockA) { synchronized(lockB) { transfer(); } }"},
        {"type": "incorrect_retry",   "code": "// BUG: retrying non-idempotent operation\npublic void chargeCard() {\n    for (int i = 0; i < 3; i++) {\n        try { stripe.charge(); break; } catch (Exception e) { /* retry */ }\n    }\n}"},
    ],
    "go": [
        {"type": "goroutine_leak",    "code": "// BUG: goroutine leak - channel never read\nfunc process() {\n\tch := make(chan int)\n\tgo func() { ch <- 42 }()\n\t// ch is never read\n}"},
        {"type": "race_condition",    "code": "// BUG: data race on shared map\nvar cache = map[string]int{}\nfunc Set(k string, v int) { cache[k] = v }"},
        {"type": "missing_error",     "code": "// BUG: error ignored\nfunc readFile(path string) []byte {\n\tdata, _ := os.ReadFile(path)\n\treturn data\n}"},
    ],
    "javascript": [
        {"type": "memory_leak",       "code": "// BUG: event listeners never removed\nfunction init() {\n  document.addEventListener('click', heavyHandler);\n}"},
        {"type": "callback_hell",     "code": "// BUG: unhandled promise rejection\nasync function fetchData() {\n  const res = await fetch('/api/data');\n  return res.json();\n  // no error handling\n}"},
        {"type": "prototype_pollution","code": "// BUG: prototype pollution\nfunction merge(target, source) {\n  for (let key in source) {\n    target[key] = source[key];\n  }\n}"},
    ],
    "typescript": [
        {"type": "any_abuse",         "code": "// BUG: excessive use of 'any' defeats type safety\nexport function processData(data: any): any {\n  return data.items.map((x: any) => x.value);\n}"},
        {"type": "missing_null_check","code": "// BUG: optional chaining missing\nexport function getUsername(user: User | null): string {\n  return user.profile.username;\n}"},
    ],
}

# --- Technical Debt Templates ------------------------------------------------

DEBT_TEMPLATES = [
    {"type": "dead_api",              "description": "Endpoint registered but never called by any client"},
    {"type": "duplicate_utility",     "description": "Same string utility function exists in two services"},
    {"type": "deprecated_endpoint",   "description": "Endpoint marked @Deprecated but still functional"},
    {"type": "copy_pasted_class",     "description": "Class duplicated across services with minor differences"},
    {"type": "legacy_pattern",        "description": "Old callback-style code in otherwise async/await codebase"},
    {"type": "unused_terraform",      "description": "Terraform module defined but never referenced"},
    {"type": "unreachable_page",      "description": "React page component with no route pointing to it"},
    {"type": "duplicate_migration",   "description": "Two SQL migrations creating the same index"},
    {"type": "config_drift",          "description": "Staging and production configs with inconsistent values"},
    {"type": "hidden_feature_flag",   "description": "Feature flag in code but not in flag management system"},
    {"type": "circular_dependency",   "description": "Service A depends on B which depends on A"},
    {"type": "stale_documentation",   "description": "README references API endpoints that no longer exist"},
]
