# FRIDAY OS - Architecture Documentation

## Core Design Philosophy
FRIDAY OS is designed as a centralized multi-agent operating system. It operates on a pipeline pattern rather than purely reactive generation, ensuring tasks are analysed, planned, executed, and verified.

## Tech Stack
- **Language**: Python 3.12+
- **Framework**: FastAPI (Async API layer)
- **Database**: SQLite (via `aiosqlite`) and SQLAlchemy 2.0 (ORM)
- **Validation**: Pydantic v2
- **Logging**: Structlog
- **Testing**: Pytest & anyio

## Directory Structure
- `backend/`
  - `config.py` - Application configuration and Pydantic Settings.
  - `main.py` - FastAPI entry point and lifecycle management.
  - `dependencies.py` - FastAPI dependency injection.
  - `database/` - ORM models, session factories, and repositories.
  - `utils/` - Shared helpers, formatters, logging, and exceptions.
  - `tests/` - Pytest suites.
- `docs/` - System documentation.
- `data/` - SQLite database, log files, and persistent state.

## Execution Pipeline
1. **Understand**: Natural language parsing.
2. **Analyze**: Capability matching.
3. **Plan**: Task breakdown.
4. **Execute**: Agent delegation.
5. **Verify**: Automated checks.
6. **Report**: Final user output.
