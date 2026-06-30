# FRIDAY OS

**FRIDAY OS** is a production-ready AI Operating System, inspired by Iron Man's JARVIS and FRIDAY. 
It is not merely a chatbot, but a complete autonomous system designed to understand natural language, remember context, reason, plan, execute tasks, control the computer, automate workflows, and verify results.

This repository currently contains **Phase 1: Foundation**.

## Current Features
- **Robust Architecture**: Built with FastAPI and SQLAlchemy 2.0.
- **Config & DI**: Centralized environment validation (Pydantic Settings) and dependency injection.
- **Database Engine**: Async SQLite (aiosqlite) with automated session management and scoping.
- **ORM Schema**: 8 declarative tables (User, Conversation, Message, Task, AgentLog, Memory, SecurityAudit, Setting).
- **Repositories**: Clean data access patterns via the Repository design pattern.
- **Utils Module**: Comprehensive exceptions, validators, helpers, and structured logging via `structlog`.

## Next Phases
- **Phase 2**: Core Services (LLMs, Vector DB, Security Rules)
- **Phase 3**: Capabilities (Voice, Automation, Web Browsing)
- **Phase 4**: Agent Orchestration
- **Phase 5**: UI and API Delivery
