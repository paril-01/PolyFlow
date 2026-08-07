# Folder Organization

## Purpose
Define consistent project structure standards to make codebases navigable and predictable.

## General Principles

1. **Consistency** — all projects in the organization follow the same structural patterns
2. **Discoverability** — a new engineer can find what they need without asking
3. **Separation of concerns** — group by feature or layer, not by file type
4. **Flat over nested** — avoid deep nesting (max 4 levels recommended)

## Recommended Structure (Feature-Based)

```
project/
├── src/                    # Source code
│   ├── features/           # Feature modules
│   │   ├── auth/           # Authentication feature
│   │   │   ├── routes.py
│   │   │   ├── service.py
│   │   │   ├── models.py
│   │   │   └── tests/
│   │   └── tasks/          # Tasks feature
│   │       ├── routes.py
│   │       ├── service.py
│   │       ├── models.py
│   │       └── tests/
│   ├── shared/             # Shared utilities
│   │   ├── database.py
│   │   ├── auth.py
│   │   └── logging.py
│   └── config/             # Configuration
│       ├── settings.py
│       └── constants.py
├── tests/                  # Integration/E2E tests
├── docs/                   # Documentation
├── scripts/                # Build/deploy scripts
├── migrations/             # Database migrations
└── config/                 # Environment configs
```

## Naming Rules

- Directories: `kebab-case` or `snake_case` (pick one, be consistent)
- Source files: Follow language convention
- Test files: Mirror source file names with `test_` prefix or `.test.` suffix
- Config files: Descriptive names matching their purpose
