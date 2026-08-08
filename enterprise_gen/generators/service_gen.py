"""
Service Scaffolding Generator.

Creates directory structures, package manifests, boilerplate files,
Dockerfiles, and README files for each service in the ECP.
"""

import os
from pathlib import Path
from typing import Dict, List
from enterprise_gen.config import ServiceDef, SERVICES, SHARED_MODULES


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# --- Package Manifest Templates ----------------------------------------------

def _package_json(svc: ServiceDef) -> str:
    if svc.framework == "react":
        return f'''{{"name": "{svc.name}","version": "2.4.1","private": true,"dependencies": {{"react": "^18.2.0","react-dom": "^18.2.0","react-router-dom": "^6.20.0","@tanstack/react-query": "^5.8.0","axios": "^1.6.2","tailwindcss": "^3.3.6","typescript": "^5.3.2"}},"scripts": {{"dev": "vite","build": "tsc && vite build","test": "vitest","lint": "eslint src/"}}}}'''
    elif svc.framework == "angular":
        return f'''{{"name": "{svc.name}","version": "1.8.0","dependencies": {{"@angular/core": "^17.0.0","@angular/router": "^17.0.0","@angular/material": "^17.0.0","rxjs": "^7.8.0","typescript": "^5.3.2"}},"scripts": {{"start": "ng serve","build": "ng build","test": "ng test"}}}}'''
    else:
        return f'''{{"name": "{svc.name}","version": "1.6.3","dependencies": {{"express": "^4.18.2","bull": "^4.12.0","nodemailer": "^6.9.7","winston": "^3.11.0","uuid": "^9.0.0"}},"scripts": {{"start": "node src/index.js","dev": "nodemon src/index.js","test": "jest"}}}}'''


def _go_mod(svc: ServiceDef) -> str:
    return f"""module github.com/ecp/{svc.name}

go 1.21

require (
\tgithub.com/go-chi/chi/v5 v5.0.11
\tgoogle.golang.org/grpc v1.60.0
\tgoogle.golang.org/protobuf v1.31.0
\tgithub.com/jackc/pgx/v5 v5.5.1
\tgithub.com/rs/zerolog v1.31.0
\tgithub.com/stretchr/testify v1.8.4
)
"""


def _pom_xml(svc: ServiceDef) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
    </parent>
    <groupId>com.ecp</groupId>
    <artifactId>{svc.name}</artifactId>
    <version>1.5.0</version>
    <dependencies>
        <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency>
        <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-data-jpa</artifactId></dependency>
        <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-security</artifactId></dependency>
        <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-validation</artifactId></dependency>
        <dependency><groupId>io.jsonwebtoken</groupId><artifactId>jjwt-api</artifactId><version>0.12.3</version></dependency>
        <dependency><groupId>org.postgresql</groupId><artifactId>postgresql</artifactId><scope>runtime</scope></dependency>
        <dependency><groupId>org.projectlombok</groupId><artifactId>lombok</artifactId><optional>true</optional></dependency>
        <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-test</artifactId><scope>test</scope></dependency>
    </dependencies>
</project>"""


def _requirements_txt(svc: ServiceDef) -> str:
    base = "fastapi==0.104.1\nuvicorn==0.24.0\npydantic==2.5.2\nsqlalchemy==2.0.23\nalembic==1.13.0\nhttpx==0.25.2\npytest==7.4.3\n"
    if "pricing" in svc.name or "recommendation" in svc.name or "ai" in svc.name:
        base += "scikit-learn==1.3.2\nnumpy==1.26.2\npandas==2.1.4\n"
    if "ai" in svc.name:
        base += "transformers==4.36.0\ntorch==2.1.1\nfaiss-cpu==1.7.4\nsentence-transformers==2.2.2\n"
    return base


def _pubspec_yaml(svc: ServiceDef) -> str:
    return """name: ecp_mobile
description: Enterprise Commerce Platform Mobile App
version: 1.2.0+3
environment:
  sdk: '>=3.2.0 <4.0.0'
dependencies:
  flutter:
    sdk: flutter
  dio: ^5.4.0
  provider: ^6.1.1
  go_router: ^12.1.1
  flutter_riverpod: ^2.4.9
"""


def _dockerfile(svc: ServiceDef) -> str:
    if svc.language == "python":
        return f"""FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE {svc.port}
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{svc.port}"]
"""
    elif svc.language == "go":
        return f"""FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /server ./cmd/main.go

FROM alpine:3.19
COPY --from=builder /server /server
EXPOSE {svc.port}
ENTRYPOINT ["/server"]
"""
    elif svc.language == "java":
        return f"""FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /app
COPY pom.xml .
COPY src src
RUN ./mvnw package -DskipTests

FROM eclipse-temurin:21-jre-alpine
COPY --from=builder /app/target/*.jar /app.jar
EXPOSE {svc.port}
ENTRYPOINT ["java", "-jar", "/app.jar"]
"""
    elif svc.language == "typescript" and svc.framework == "react":
        return """FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 3000
"""
    elif svc.language == "javascript":
        return f"""FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production
COPY . .
EXPOSE {svc.port}
CMD ["node", "src/index.js"]
"""
    return f"FROM ubuntu:22.04\nEXPOSE {svc.port}\n"


def _readme(svc: ServiceDef) -> str:
    return f"""# {svc.name}

{svc.description}

## Team
{svc.team}

## Tech Stack
- **Language**: {svc.language}
- **Framework**: {svc.framework}
- **Port**: {svc.port}

## Dependencies
{chr(10).join(f'- `{d}`' for d in svc.depends_on) if svc.depends_on else 'None'}

## Getting Started

```bash
# Install dependencies
# (language-specific command)

# Run in development
# (language-specific command)

# Run tests
# (language-specific command)
```

## API Endpoints

See the OpenAPI spec in `docs/openapi.yaml`.
"""


def _gitignore() -> str:
    return """# Dependencies
node_modules/
__pycache__/
*.pyc
target/
.gradle/
vendor/
.dart_tool/

# Build outputs
dist/
build/
*.class
*.jar

# IDE
.idea/
.vscode/
*.swp

# Environment
.env
.env.local
*.log

# OS
.DS_Store
Thumbs.db

# Terraform
.terraform/
*.tfstate
*.tfstate.*
"""


# --- Main Generator ----------------------------------------------------------

def generate_service_scaffolding(output_dir: Path):
    """Generate directory structures and boilerplate for all services."""
    print(f"  Generating service scaffolding in {output_dir}")

    # Root files
    _write(output_dir / ".gitignore", _gitignore())
    _write(output_dir / "README.md", f"# Enterprise Commerce Platform (ECP)\n\nA synthetic polyglot enterprise with {len(SERVICES)} services across 15+ languages.\nGenerated by the PolyFlow Synthetic Enterprise Generator.\n")
    _write(output_dir / "docker-compose.yml", _docker_compose())

    # Generate each service
    for svc in SERVICES:
        svc_dir = output_dir / svc.name
        svc_dir.mkdir(parents=True, exist_ok=True)

        # Package manifest
        if svc.package_file == "package.json":
            _write(svc_dir / "package.json", _package_json(svc))
        elif svc.package_file == "go.mod":
            _write(svc_dir / "go.mod", _go_mod(svc))
        elif svc.package_file == "pom.xml":
            _write(svc_dir / "pom.xml", _pom_xml(svc))
        elif svc.package_file == "requirements.txt":
            _write(svc_dir / "requirements.txt", _requirements_txt(svc))
        elif svc.package_file == "pubspec.yaml":
            _write(svc_dir / "pubspec.yaml", _pubspec_yaml(svc))

        # Dockerfile
        _write(svc_dir / "Dockerfile", _dockerfile(svc))

        # README
        _write(svc_dir / "README.md", _readme(svc))

        # Source directory
        src = svc_dir / svc.src_dir
        src.mkdir(parents=True, exist_ok=True)

        # Config files
        if svc.language == "python":
            _write(svc_dir / "app" / "__init__.py", f'"""ECP {svc.name} service."""\n')
            _write(svc_dir / "app" / "main.py", _python_main(svc))
            _write(svc_dir / "app" / "config.py", _python_config(svc))
            _write(svc_dir / "app" / "models" / "__init__.py", "")
            _write(svc_dir / "app" / "routes" / "__init__.py", "")
            _write(svc_dir / "app" / "services" / "__init__.py", "")
            _write(svc_dir / "tests" / "__init__.py", "")
        elif svc.language == "go":
            _write(svc_dir / "cmd" / "main.go", _go_main(svc))
            _write(svc_dir / "internal" / "handler" / ".gitkeep", "")
            _write(svc_dir / "internal" / "service" / ".gitkeep", "")
            _write(svc_dir / "internal" / "model" / ".gitkeep", "")
            _write(svc_dir / "internal" / "repository" / ".gitkeep", "")
        elif svc.language == "java":
            pkg = svc_dir / "src" / "main" / "java" / "com" / "ecp" / svc.name.replace("-", "")
            pkg.mkdir(parents=True, exist_ok=True)
            _write(pkg / "Application.java", _java_main(svc))
            (pkg / "controller").mkdir(exist_ok=True)
            (pkg / "service").mkdir(exist_ok=True)
            (pkg / "model").mkdir(exist_ok=True)
            (pkg / "repository").mkdir(exist_ok=True)
            (pkg / "config").mkdir(exist_ok=True)
            _write(svc_dir / "src" / "main" / "resources" / "application.yml", _java_config(svc))
            _write(svc_dir / "src" / "test" / "java" / ".gitkeep", "")
        elif svc.framework == "react":
            _write(svc_dir / "src" / "App.tsx", _react_app())
            _write(svc_dir / "src" / "index.tsx", "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\nReactDOM.createRoot(document.getElementById('root')!).render(<App />);\n")
            _write(svc_dir / "src" / "pages" / ".gitkeep", "")
            _write(svc_dir / "src" / "components" / ".gitkeep", "")
            _write(svc_dir / "src" / "hooks" / ".gitkeep", "")
            _write(svc_dir / "src" / "services" / "api.ts", "import axios from 'axios';\nexport const api = axios.create({ baseURL: '/api/v1' });\n")
            _write(svc_dir / "tsconfig.json", '{"compilerOptions":{"target":"ES2020","module":"ESNext","jsx":"react-jsx","strict":true}}')
        elif svc.framework == "angular":
            _write(svc_dir / "src" / "app" / "app.module.ts", _angular_app())
            _write(svc_dir / "src" / "app" / "app.component.ts", "import { Component } from '@angular/core';\n@Component({selector:'app-root',template:'<router-outlet></router-outlet>'})\nexport class AppComponent {}\n")
            _write(svc_dir / "src" / "app" / "pages" / ".gitkeep", "")
            _write(svc_dir / "src" / "app" / "services" / ".gitkeep", "")
            _write(svc_dir / "tsconfig.json", '{"compilerOptions":{"target":"ES2022","module":"ES2022","strict":true}}')
        elif svc.language == "javascript":
            _write(svc_dir / "src" / "index.js", _node_main(svc))
            _write(svc_dir / "src" / "routes" / ".gitkeep", "")
            _write(svc_dir / "src" / "services" / ".gitkeep", "")
            _write(svc_dir / "src" / "templates" / ".gitkeep", "")

    # Shared modules
    for mod in SHARED_MODULES:
        mod_dir = output_dir / mod["name"]
        mod_dir.mkdir(parents=True, exist_ok=True)
        _write(mod_dir / "README.md", f"# {mod['name']}\n\n{mod['description']}\n")

    print(f"  [OK] Generated {len(SERVICES)} service directories + {len(SHARED_MODULES)} shared modules")


# --- Language-specific entry points ------------------------------------------

def _python_main(svc: ServiceDef) -> str:
    return f'''"""ECP {svc.name} — FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="{svc.name}", version="1.5.0", description="{svc.description}")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {{"service": "{svc.name}", "status": "healthy", "version": "1.5.0"}}
'''

def _python_config(svc: ServiceDef) -> str:
    return f'''"""Service configuration."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/{svc.name.replace("-","_")}")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SERVICE_PORT = {svc.port}
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
'''

def _go_main(svc: ServiceDef) -> str:
    return f'''package main

import (
\t"fmt"
\t"log"
\t"net/http"
\t"github.com/go-chi/chi/v5"
\t"github.com/go-chi/chi/v5/middleware"
)

func main() {{
\tr := chi.NewRouter()
\tr.Use(middleware.Logger)
\tr.Use(middleware.Recoverer)

\tr.Get("/health", func(w http.ResponseWriter, r *http.Request) {{
\t\tw.Write([]byte(`{{"service":"{svc.name}","status":"healthy"}}`))\n\t}})

\taddr := ":{svc.port}"
\tfmt.Printf("{svc.name} listening on %s\\n", addr)
\tlog.Fatal(http.ListenAndServe(addr, r))
}}
'''

def _java_main(svc: ServiceDef) -> str:
    cls = "".join(w.capitalize() for w in svc.name.replace("-", " ").split())
    return f'''package com.ecp.{svc.name.replace("-","")};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class {cls}Application {{
    public static void main(String[] args) {{
        SpringApplication.run({cls}Application.class, args);
    }}
}}
'''

def _java_config(svc: ServiceDef) -> str:
    return f"""server:
  port: {svc.port}
spring:
  application:
    name: {svc.name}
  datasource:
    url: jdbc:postgresql://localhost:5432/{svc.name.replace("-","_")}
    username: ecp
    password: ecp_secret
  jpa:
    hibernate:
      ddl-auto: validate
logging:
  level:
    root: INFO
    com.ecp: DEBUG
"""

def _node_main(svc: ServiceDef) -> str:
    return f'''const express = require('express');
const {{ v4: uuidv4 }} = require('uuid');
const winston = require('winston');

const app = express();
const PORT = process.env.PORT || {svc.port};

const logger = winston.createLogger({{
  level: 'info',
  format: winston.format.json(),
  transports: [new winston.transports.Console()],
}});

app.use(express.json());

app.get('/health', (req, res) => {{
  res.json({{ service: '{svc.name}', status: 'healthy', version: '1.6.3' }});
}});

app.listen(PORT, () => {{
  logger.info(`{svc.name} listening on port ${{PORT}}`);
}});
'''

def _react_app() -> str:
    return '''import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <h1 className="text-xl font-bold text-gray-900">ECP Store</h1>
          </div>
        </nav>
        <Routes>
          <Route path="/" element={<div className="p-8"><h2>Welcome to ECP</h2></div>} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
'''

def _angular_app() -> str:
    return '''import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { AppComponent } from './app.component';

@NgModule({
  declarations: [AppComponent],
  imports: [BrowserModule, RouterModule.forRoot([]), HttpClientModule],
  bootstrap: [AppComponent],
})
export class AppModule {}
'''


def _docker_compose() -> str:
    lines = ["version: '3.9'", "", "services:"]
    for svc in SERVICES:
        lines.append(f"  {svc.name}:")
        lines.append(f"    build: ./{svc.name}")
        if svc.port:
            lines.append(f"    ports:")
            lines.append(f'      - "{svc.port}:{svc.port}"')
        if svc.depends_on:
            lines.append(f"    depends_on:")
            for dep in svc.depends_on[:3]:
                lines.append(f"      - {dep}")
        lines.append(f"    environment:")
        lines.append(f"      - LOG_LEVEL=INFO")
        lines.append("")

    lines.append("  postgres:")
    lines.append("    image: postgres:16-alpine")
    lines.append("    ports:")
    lines.append('      - "5432:5432"')
    lines.append("    environment:")
    lines.append("      POSTGRES_USER: ecp")
    lines.append("      POSTGRES_PASSWORD: ecp_secret")
    lines.append("")
    lines.append("  redis:")
    lines.append("    image: redis:7-alpine")
    lines.append("    ports:")
    lines.append('      - "6379:6379"')

    return "\n".join(lines) + "\n"
