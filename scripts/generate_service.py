#!/usr/bin/env python3
"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Service Template Generator — scaffolds a new CortexOS microservice.

Usage:
    python scripts/generate_service.py <service-name>

Example:
    python scripts/generate_service.py finance-service
"""

import os
import sys
import textwrap

HEADER = '''"""
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
"""'''


def generate_service(service_name: str):
    """Generate a new microservice directory structure."""
    label = service_name.replace("-", " ").title().replace(" ", " ")
    class_name = (
        service_name.replace("-service", "").replace("-", " ").title().replace(" ", "")
    )
    base_dir = os.path.join("backend", "services", service_name, "app")

    dirs = [
        os.path.join(base_dir, "api"),
        os.path.join(base_dir, "config"),
        os.path.join(base_dir, "events"),
        os.path.join(base_dir, "models"),
        os.path.join(base_dir, "repositories"),
        os.path.join(base_dir, "schemas"),
        os.path.join(base_dir, "services"),
    ]

    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # __init__.py for each package
    for d in [base_dir] + dirs:
        init_path = os.path.join(d, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write(f"{HEADER}\n")

    # main.py
    with open(os.path.join(base_dir, "main.py"), "w") as f:
        f.write(textwrap.dedent(f"""\
            {HEADER}

            from contextlib import asynccontextmanager

            from fastapi import FastAPI, Request
            from fastapi.responses import JSONResponse

            from app.api.routes import router as api_router

            from backend.shared.logging.logger import get_logger
            from backend.shared.messaging.producer import get_producer, close_producer

            logger = get_logger("{service_name}")


            @asynccontextmanager
            async def lifespan(app: FastAPI):
                logger.info("{label} starting up")
                try:
                    await get_producer()
                    logger.info("Kafka producer initialized")
                except Exception as exc:
                    logger.warning(f"Kafka producer not available: {{exc}}")
                yield
                logger.info("{label} shutting down")
                await close_producer()


            app = FastAPI(
                title="{label}",
                description="CortexOS {label}",
                version="1.0.0",
                lifespan=lifespan,
            )

            app.include_router(api_router)


            @app.exception_handler(Exception)
            async def global_exception_handler(request: Request, exc: Exception):
                logger.error(f"Unhandled exception: {{exc}}", exc_info=True)
                return JSONResponse(status_code=500, content={{"status": "error", "error": {{"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}}}})


            @app.get("/health")
            async def health_check():
                return {{"status": "healthy", "service": "{service_name}"}}


            @app.get("/metrics")
            async def metrics():
                return {{"status": "success", "data": {{"service": "{service_name}", "version": "1.0.0"}}}}
        """))

    # routes.py
    with open(os.path.join(base_dir, "api", "routes.py"), "w") as f:
        f.write(textwrap.dedent(f"""\
            {HEADER}

            from fastapi import APIRouter

            router = APIRouter()


            @router.get("/", tags=["{label}"])
            async def root():
                return {{"service": "{service_name}", "status": "running"}}
        """))

    # model.py
    with open(os.path.join(base_dir, "models", "model.py"), "w") as f:
        f.write(
            f"{HEADER}\n\n# ORM models for {label}\n# from backend.shared.database.base_model import Base, TimestampMixin\n"
        )

    # schema.py
    with open(os.path.join(base_dir, "schemas", "schema.py"), "w") as f:
        f.write(
            f'{HEADER}\n\nfrom pydantic import BaseModel\n\n\nclass {class_name}Base(BaseModel):\n    """Base schema for {label}."""\n    pass\n'
        )

    # repository.py
    with open(os.path.join(base_dir, "repositories", "repository.py"), "w") as f:
        f.write(
            f'{HEADER}\n\n\nclass {class_name}Repository:\n    """Data access layer for {label}."""\n    pass\n'
        )

    # service_logic.py
    with open(os.path.join(base_dir, "services", "service_logic.py"), "w") as f:
        f.write(
            f'{HEADER}\n\n\nclass {class_name}Service:\n    """Core business logic for {label}."""\n    pass\n'
        )

    # events.py
    with open(os.path.join(base_dir, "events", "events.py"), "w") as f:
        f.write(
            f"{HEADER}\n\nfrom backend.shared.messaging.schemas import BaseEvent\n\n# Define event classes for {label} here\n"
        )

    # config/settings.py
    with open(os.path.join(base_dir, "config", "settings.py"), "w") as f:
        f.write(textwrap.dedent(f'''\
            {HEADER}

            from backend.shared.config.settings import CortexOSSettings


            class {class_name}Settings(CortexOSSettings):
                """Service-specific settings for {label}."""

                model_config = {{
                    "env_prefix": "{class_name.upper()}_",
                    "env_file": ".env",
                    "env_file_encoding": "utf-8",
                    "case_sensitive": False,
                }}
        '''))

    # requirements.txt
    svc_dir = os.path.join("backend", "services", service_name)
    with open(os.path.join(svc_dir, "requirements.txt"), "w") as f:
        f.write(
            "fastapi==0.103.2\\nuvicorn[standard]==0.23.2\\nsqlalchemy[asyncio]==2.0.23\\nasyncpg==0.29.0\\nredis==5.0.1\\naiokafka==0.10.0\\npydantic==2.5.3\\npydantic-settings==2.1.0\\npython-jose[cryptography]==3.3.0\\nalembic==1.13.1\\n"
        )

    # Dockerfile
    with open(os.path.join(svc_dir, "Dockerfile"), "w") as f:
        f.write(textwrap.dedent(f"""\
            # CortexOS — Copyright (c) 2026 Saravana Perumal K — AGPL v3

            FROM python:3.11-slim

            WORKDIR /app

            RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
            RUN pip install poetry

            COPY pyproject.toml /app/
            RUN poetry config virtualenvs.create false && poetry install --only main --no-root

            COPY shared /app/shared
            COPY services/{service_name}/app /app/app

            EXPOSE 8000
            CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
        """))

    print(f"✅ Service '{service_name}' generated at {svc_dir}/")
    print("   Structure:")
    for d in sorted(dirs):
        print(f"   ├── {os.path.relpath(d, svc_dir)}/")
    print("   ├── Dockerfile")
    print("   └── requirements.txt")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/generate_service.py <service-name>")
        print("Example: python scripts/generate_service.py finance-service")
        sys.exit(1)

    name = sys.argv[1]
    if not name.endswith("-service"):
        name += "-service"

    generate_service(name)
