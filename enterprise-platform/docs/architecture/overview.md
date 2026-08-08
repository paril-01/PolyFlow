# ECP Architecture Overview

## Services
- **frontend-react**: Customer Portal (React 18 + TypeScript) (typescript/react)
- **frontend-angular**: Admin Dashboard (Angular 17 + TypeScript) (typescript/angular)
- **mobile-flutter**: Mobile App (Flutter + Dart) (dart/flutter)
- **gateway-go**: API Gateway (Go + Chi + GraphQL) (go/chi)
- **auth-service-java**: Authentication & Authorization (Spring Boot 3) (java/spring-boot)
- **payment-service-java**: Payment Processing (Spring Boot 3 + Stripe) (java/spring-boot)
- **order-service-go**: Order Management (Go + gRPC) (go/grpc)
- **inventory-python**: Inventory Management (Python FastAPI) (python/fastapi)
- **pricing-python**: Dynamic Pricing Engine (Python FastAPI + ML) (python/fastapi)
- **recommendation-python**: Recommendation Engine (Python + scikit-learn) (python/fastapi)
- **notification-node**: Notification Service (Node.js + Express + Bull) (javascript/express)
- **analytics-java**: Analytics & Reporting (Spring Boot + Kafka) (java/spring-boot)
- **ai-service-python**: AI/NLP Service (Python + Transformers + FAISS) (python/fastapi)

## Call Chains
- **customer_purchase_flow**: Customer adds items to cart, checks out, payment processed, notifications sent
- **admin_product_update**: Admin updates product in dashboard, triggers inventory sync and price recalculation
- **ai_search_flow**: Customer searches for a product using natural language, AI processes query
- **order_return_flow**: Customer initiates a return, inventory restocked, refund processed
- **fraud_detection_flow**: Payment triggers AI fraud scoring, blocks suspicious transactions

## Technology Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Angular 17, Flutter |
| Gateway | Go + Chi + GraphQL |
| Backend | Spring Boot 3, FastAPI, Express |
| ML/AI | scikit-learn, Transformers, FAISS |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Queue | Kafka, Bull |
| Infrastructure | Terraform, Kubernetes, Docker |
| Monitoring | Prometheus, Grafana |
| CI/CD | GitHub Actions |
