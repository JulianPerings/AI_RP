# API Directory

**Purpose**: API layer containing route handlers for the FastAPI application.

## Structure
- `routes/` - Individual route modules for each resource type
- `__init__.py` - Empty package marker

## Pattern
Each route module in `routes/` corresponds to a database model and provides CRUD endpoints.
All routers are exported via `routes/__init__.py` for clean imports.
