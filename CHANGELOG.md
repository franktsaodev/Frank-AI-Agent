# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows
Semantic Versioning.

## [Unreleased]

## [1.0.1] - 2026-08-08

### Added

- Comprehensive project README
- Architecture overview diagram
- Agent execution flow diagram
- Session lifecycle diagram
- MIT license
- Project changelog
- Dedicated health API routes
- Chat agent factory provider for API dependency injection

### Changed

- Refactored API dependency wiring for clearer separation of responsibilities
- Reorganized health and session API routes
- Simplified application bootstrap responsibilities
- Cleaned up obsolete API and service modules
- Improved session manager tests and reusable test fakes
- Improved session isolation integration tests
- Updated runtime and development dependencies
- Updated Docker and Docker Compose configuration
- Updated environment configuration examples
- Improved repository ignore rules
- Rewritten project documentation covering architecture, configuration,
  REST API, Docker, testing, and development roadmap
- Updated repository references for the `franktsaodev` GitHub account

### Removed

- Obsolete `chat_agent_factory_dependencies` API module
- Legacy API routes module
- Unused services package initialization

## [1.0.0] - 2026-08-06

First stable release of the Frank AI Agent framework.

### Added

- Stateful agent session architecture
- Session-isolated `ChatAgent` instances
- Conversation memory with sliding-window history
- Structured fact memory
- Configurable memory policies
- Fact extraction pipeline
- Iterative LLM tool-calling workflow
- Centralized tool registry and tool execution
- Plugin-based tool architecture
- Structured tracing for agent, LLM, and tool lifecycle events
- Logging and JSON trace exporters
- Environment-based runtime configuration
- Typed configuration models and configuration loaders
- FastAPI REST API
- Session creation, chat, history, detail, and deletion endpoints
- Centralized API exception handling
- Session TTL and sliding expiration
- Background cleanup of expired sessions
- Runtime health endpoint
- Swagger UI, ReDoc, and OpenAPI documentation
- Docker image support
- Docker Compose deployment
- Container health checks
- Unit and integration test suites
- Ruff linting and formatting
- Pyright static type checking

## Development Milestones

The following pre-1.0 versions represent internal development milestones
leading to the first stable release.

## [0.9.0] - 2026-08-05

### Added

- Dockerfile
- Docker Compose configuration
- FastAPI container deployment
- Container health checks
- Runtime application metadata

## [0.8.0] - 2026-08-05

### Added

- FastAPI application layer
- Versioned REST API
- Health endpoint
- Session-based chat routes
- Centralized exception handlers
- OpenAPI documentation

## [0.7.0] - 2026-08-05

### Added

- Environment-based configuration architecture
- Typed configuration models
- Configuration loaders
- Runtime dependency construction
- Application bootstrap composition

## [0.6.0] - 2026-08-04

### Added

- Prompt composition pipeline
- Fact extraction
- Memory policies
- Tool plugin architecture
- Tool registry and execution
- Structured tracing foundation