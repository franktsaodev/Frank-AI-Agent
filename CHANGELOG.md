# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows
Semantic Versioning.

## [Unreleased]

### Added

- Added configurable CORS support for browser-based frontend clients.
- Added a React frontend with API health checks, isolated session initialization, and an interactive chat interface.

## [1.2.0] - 2026-09-03

### Added

- Added configurable runtime log levels.
- Added keyword-based conditional retrieval.
- Added source attribution with PDF page metadata.
- Added trusted citation tokens and response validation to prevent hallucinated source names and page numbers.
- Added configurable minimum cosine similarity filtering for retrieval results.
- Added recursive boundary-aware text splitting with paragraph, newline, word, and character fallbacks.
- Added a deterministic grounded fallback when triggered retrieval returns no usable context.
- Added a semantic retrieval quality baseline covering Recall@3 and irrelevant-query rejection.

### Changed

- Changed Docker Compose to persist the Hugging Face model cache.
- Changed the default retrieval knowledge path to the knowledge directory.
- Changed the retrieval runtime to use recursive boundary-aware text splitting while retaining fixed-size splitter support.

### Fixed

- Updated the default Groq model configuration.
- Aligned retrieval threshold validation with the cosine similarity range.

## [1.1.0] - 2026-08-13

### Added

- Added retrieval-augmented generation (RAG) support for local knowledge bases.
- Added TXT, Markdown, and text-based PDF document loaders.
- Added recursive directory loading for supported knowledge documents.
- Added fixed-size text chunking with configurable overlap.
- Added local sentence-transformer embeddings for semantic retrieval.
- Added an in-memory vector store with cosine similarity search.
- Added semantic retrieval through `VectorStoreRetriever`.
- Added source metadata preservation for retrieved knowledge.
- Added retrieval policy abstractions for controlling knowledge lookup.
- Added retrieval context integration into `ChatAgent` and `PromptComposer`.
- Added configurable retrieval runtime through environment variables.
- Added sample knowledge documents for retrieval testing and demonstration.
- Added unit and integration coverage for the retrieval pipeline.

### Changed

- Updated agent execution flow to optionally retrieve external knowledge before prompt composition.
- Updated runtime bootstrap to construct retrieval dependencies through `RetrievalRuntimeFactory`.
- Updated README documentation with RAG architecture, configuration, runtime behavior, and roadmap.
- Improved retrieval configuration validation.
- Improved startup validation for invalid or empty knowledge sources.
- Improved document ingestion resilience by skipping individual documents that fail to load.
- Improved retrieval runtime observability with startup logging.

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