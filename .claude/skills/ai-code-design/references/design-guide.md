# Software Design Reference Guide

This reference is loaded by the `ai-code-design` skill when making architecture and design decisions. It provides pattern catalogs, component definitions, anti-pattern warnings, cross-cutting concern guidance, and a greenfield decision framework. All content is platform-agnostic — adapt to the project's stack as indicated by `.context/README.md`.

---

## 1. Architecture Patterns

### Clean Architecture (Robert C. Martin)

**Structure:** Concentric layers with the Dependency Rule — source code dependencies point inward only. Outer layers know about inner layers; inner layers never reference outer layers.

**Layers (inside → out):**
1. **Entities** — Enterprise-wide business rules. Domain objects with identity and behavior. These are the most stable — they change only when fundamental business rules change.
2. **Use Cases** — Application-specific business rules. Each use case orchestrates entities and defines the application's behavior for a single user intention (e.g., `PlaceOrder`, `TransferFunds`).
3. **Interface Adapters** — Format conversion. Controllers translate HTTP requests into use-case inputs. Presenters translate use-case outputs into view models. Gateways translate domain interfaces into database calls.
4. **Frameworks & Drivers** — External tools: database engines, web frameworks, UI frameworks, external APIs. These are implementation details that can be swapped without touching business logic.

**When to use:**
- Moderate-to-high domain complexity
- Testability is a priority (domain logic testable in isolation)
- Long-lived project where frameworks may change
- Team is familiar with layered patterns

**Anti-pattern — Framework Coupling:** Domain entities import framework annotations (e.g., ORM decorators, HTTP framework types). This inverts the dependency rule and makes the domain untestable without the framework. Fix: use plain domain objects and map to framework-specific representations at the adapter layer.

**Anti-pattern — Use Case Bloat:** A single use case class accumulates dozens of methods. This violates Single Responsibility. Fix: one class per use case, named after the user intention.

### Hexagonal Architecture (Ports and Adapters, Alistair Cockburn)

**Structure:** The application core defines its own interfaces ("ports") for both inbound and outbound interactions. Infrastructure provides "adapters" that implement these ports.

**Key concepts:**
- **Driving Ports** (primary) — Interfaces the core exposes to the outside world. Example: `OrderService` interface that a REST controller calls.
- **Driven Ports** (secondary) — Interfaces the core requires from the outside world. Example: `OrderRepository` interface that the core calls, implemented by a database adapter.
- **Adapters** — Concrete implementations that connect ports to infrastructure. A `PostgresOrderRepository` adapter implements the `OrderRepository` driven port.

**When to use:**
- High domain complexity with rich business rules
- Multiple entry points (REST API, CLI, message queue, scheduled jobs)
- Multiple persistence backends or external service integrations
- Strong emphasis on testability — the core is testable with in-memory adapters

**Anti-pattern — Port Explosion:** Defining a separate port interface for every single method or operation. This creates excessive abstraction without benefit. Fix: group related operations into cohesive port interfaces (e.g., `OrderRepository` with `save`, `findById`, `findByStatus`).

**Anti-pattern — Adapter Logic:** Business logic creeps into adapter implementations (e.g., validation in the controller, business rules in the repository). Fix: adapters translate only — all logic lives in the core.

### Layered / N-Tier Architecture

**Structure:** Horizontal layers stacked top-to-bottom. Each layer depends only on the layer directly below it.

**Layers (top → bottom):**
1. **Presentation** — UI controllers, API handlers, view rendering
2. **Business Logic (BLL)** — Services, validators, domain rules, orchestration
3. **Data Access (DAL)** — Repositories, data mappers, ORM configuration, query builders

**When to use:**
- Simple CRUD applications with minimal business logic
- Small teams or solo developers
- Short-lived projects or prototypes
- When simplicity outweighs flexibility

**Improvement:** Apply Dependency Inversion between BLL and DAL — define repository interfaces in the BLL layer, implement them in the DAL layer. This gives you the simplicity of N-Tier with the testability of Clean Architecture for the business layer.

**Anti-pattern — Tight Coupling:** The business layer directly instantiates data access classes (e.g., `new PostgresRepository()`) instead of depending on interfaces. Fix: constructor injection with interface dependencies.

**Anti-pattern — Anemic Domain Model:** Entities are pure data bags (getters/setters only) while services hold all logic. This incurs the structural cost of a domain model without its benefits. Fix: move business rules into domain objects. Services should be thin orchestrators, not logic holders.

### Pattern Decision Matrix

| Factor | Layered | Clean | Hexagonal |
|--------|---------|-------|-----------|
| Domain complexity | Low | Moderate | High |
| Team size | Solo / Small | Small / Medium | Medium / Large |
| Testability needs | Standard | High | Very High |
| Multiple entry points | No | Possible | Yes |
| Framework independence | Low | High | Very High |
| Learning curve | Low | Medium | Medium-High |
| Initial setup cost | Low | Medium | Medium-High |
| Long-term flexibility | Low | High | Very High |

**Default recommendation:** When uncertain, start with Clean Architecture. It provides good testability and flexibility without the overhead of full hexagonal. You can always evolve toward hexagonal if multiple entry points or adapters emerge.

---

## 2. Component Catalog

### Domain Layer Components

| Component | Definition | Responsibility | Anti-Pattern to Avoid |
|-----------|-----------|---------------|----------------------|
| **Entity** | Object with unique identity and lifecycle | Encapsulates business rules, validates invariants, manages state transitions | Anemic Entity: data bag with no behavior; all logic in services |
| **Value Object** | Immutable object defined by its attributes, not identity | Enforces validity at construction, provides domain-meaningful operations (e.g., `Money.add()`, `Email.validate()`) | Primitive Obsession: using raw strings/numbers where a value object would enforce constraints |
| **Domain Service** | Stateless operation that doesn't belong to a single entity | Coordinates logic spanning multiple entities; contains domain rules that are not the responsibility of any one entity | God Service: a single service class accumulating all domain logic |
| **Domain Event** | Record of something meaningful that happened in the domain | Signals state transitions (e.g., `OrderPlaced`, `PaymentReceived`); enables loose coupling between domain concepts | Event Soup: emitting events for trivial state changes that don't represent business-meaningful occurrences |

### Application Layer Components

| Component | Definition | Responsibility | Anti-Pattern to Avoid |
|-----------|-----------|---------------|----------------------|
| **Use Case / Interactor** | Application-specific operation representing a single user intention | Orchestrates entities, repositories, and domain services to fulfill a use case; contains application rules (not domain rules) | Fat Use Case: embedding business rules that belong in entities or domain services |
| **Application Service** | Thin orchestration layer (alternative to explicit use cases) | Coordinates calls to repositories and domain objects; handles transactions and cross-cutting application concerns | Service Layer as Dumping Ground: application services containing domain logic, presentation logic, and data access logic |
| **Command / Query** | Input objects that represent a user's intention | Carry validated input data to use cases; separate write operations (commands) from read operations (queries) | Overuse: applying CQRS to simple CRUD where a single service method suffices |

### Adapter Layer Components

| Component | Definition | Responsibility | Anti-Pattern to Avoid |
|-----------|-----------|---------------|----------------------|
| **Controller / Handler** | Entry point for external requests | Parse input, delegate to use case, format response. Contains no business logic. | Fat Controller: validation, business rules, and data access in the controller |
| **DTO (Data Transfer Object)** | Simple structure for crossing layer boundaries | Carry data between layers without leaking domain internals. Separate inbound DTOs (request) from outbound (response). | DTO Explosion: creating a unique DTO for every minor variation instead of reusing where appropriate |
| **Presenter / Mapper** | Transforms domain objects to external representations | Convert entities to response DTOs, API responses, or view models | Leaky Abstraction: exposing database column names or ORM annotations in API responses |

### Infrastructure Layer Components

| Component | Definition | Responsibility | Anti-Pattern to Avoid |
|-----------|-----------|---------------|----------------------|
| **Repository Implementation** | Concrete data access behind a domain-defined interface | Implements the repository port using a specific technology (Postgres, MongoDB, in-memory) | Repository as Query Builder: exposing raw query construction instead of domain-meaningful methods like `findActiveByRegion()` |
| **Middleware** | Cross-cutting request pipeline behavior | Authentication, logging, rate limiting, error handling, request correlation | Middleware Overload: business logic hidden in middleware where it's invisible to the domain layer |
| **External Service Client** | Adapter for third-party APIs or services | Translates between external API contracts and internal domain interfaces | Direct Coupling: domain code calling external APIs directly without an adapter interface |
| **Configuration Provider** | Manages environment-specific settings | Loads config from environment variables, files, or secrets managers; provides typed access | Config Scatter: reading `process.env` or `os.environ` directly throughout the codebase instead of centralizing |

### Component Interaction Rules

1. **Controllers** call **Use Cases / Application Services** — never repositories or domain services directly
2. **Use Cases** call **Repositories** (via interface) and **Domain Services** — never infrastructure directly
3. **Entities** contain business rules — they call nothing external; they are self-contained
4. **Repositories** are defined as interfaces in the domain/application layer — implemented in infrastructure
5. **DTOs** exist at layer boundaries — never pass entities to controllers or database rows to use cases

---

## 3. DDD Tactical Patterns

### When to Include DDD

Include DDD tactical patterns when the Scope Assessment (Step 1) reveals:
- Complex business rules that go beyond CRUD
- Multiple domain concepts with non-trivial relationships
- Business invariants that must be enforced consistently
- Domain events that other parts of the system react to

Skip DDD patterns for simple CRUD, utility features, or infrastructure work.

### Aggregates

An aggregate is a cluster of domain objects treated as a single unit for data consistency.

**Rules:**
- Each aggregate has a single **root entity** — external code references the aggregate only through its root
- Modify only one aggregate per transaction — cross-aggregate consistency is eventually consistent
- The aggregate root enforces all invariants for the cluster
- Keep aggregates small — prefer more small aggregates over fewer large ones

**Example:** An `Order` aggregate contains `OrderLineItems`. External code accesses line items through the `Order` root, which enforces rules like "order total cannot exceed credit limit."

**Anti-pattern — Giant Aggregate:** Putting too many entities under one root (e.g., `Customer` aggregate containing `Orders`, `Addresses`, `Preferences`, `PaymentMethods`). Fix: split into separate aggregates connected by ID references, not object references.

### Bounded Contexts

A bounded context is an explicit boundary within which a domain model is defined and applicable.

**When to use:**
- The same real-world concept means different things in different parts of the system (e.g., "User" in authentication vs. "User" in billing)
- Different teams own different parts of the domain
- A model is becoming too large to reason about coherently

**Rules:**
- Each bounded context has its own ubiquitous language — the same word can mean different things across contexts
- Contexts communicate through explicit interfaces (APIs, events, shared contracts), not shared databases
- Map relationships between contexts: upstream/downstream, conformist, anti-corruption layer

### Domain Events

A domain event records that something business-meaningful happened.

**When to use:**
- Other parts of the system need to react to state changes
- You want to decouple the trigger from the reaction
- You need an audit trail of what happened in the domain

**Rules:**
- Events are immutable and past-tense (`OrderPlaced`, not `PlaceOrder`)
- Events carry the data needed by consumers — don't force consumers to call back for details
- Distinguish domain events (within a bounded context) from integration events (between contexts)

**Anti-pattern — Event Soup:** Emitting events for every trivial state change. Events should represent business-meaningful occurrences, not database update notifications.

---

## 4. Cross-Cutting Concerns

### Error Handling

**Principle:** Define errors in the domain language, map to transport representations at the boundary.

**Recommended approach:**
1. Define a domain-specific error hierarchy (e.g., `OrderNotFound`, `InsufficientInventory`, `InvalidPaymentMethod`) — not HTTP status codes or database error codes
2. Use Result/Either types for expected failures (validation errors, business rule violations). Reserve exceptions for truly exceptional situations (network failure, disk full).
3. Map domain errors to transport-specific responses at the adapter layer:
   - `OrderNotFound` → HTTP 404
   - `InsufficientInventory` → HTTP 409
   - `InvalidPaymentMethod` → HTTP 422
4. Never swallow errors silently — always log or propagate
5. Include correlation IDs in error responses for debugging

**Language patterns:**
- TypeScript: discriminated unions or `Result<T, E>` types
- Python: custom exception hierarchy or `Result` pattern (returns library)
- Java: checked exceptions for expected failures, runtime exceptions for unexpected

### Logging and Observability

**Principle:** Instrument at boundaries, not throughout domain logic.

**Recommended approach:**
1. Structured logging (JSON format) with consistent field names
2. Correlation IDs that trace requests across layers and services — generate at the edge, propagate through context
3. Three pillars of observability:
   - **Logs** — what happened (structured events at boundaries)
   - **Metrics** — how much / how fast (request count, latency, error rate)
   - **Traces** — the path through the system (distributed tracing spans)
4. Log at these points:
   - Incoming requests (controller layer)
   - Outgoing calls to external services (infrastructure layer)
   - Error paths (wherever errors are caught and handled)
   - Business-significant events (use case layer, sparingly)
5. Do not log inside domain entities or value objects — they should be pure

### Configuration Management

**Principle:** Externalize all environment-specific values. The same build artifact deploys to every environment.

**Recommended approach (12-Factor App, Factor III):**
1. Environment variables for all environment-specific configuration
2. Secrets manager for sensitive values (API keys, database credentials) — never commit secrets to source control
3. Typed configuration objects — don't sprinkle `process.env` or `os.environ` calls throughout the codebase; load once and inject
4. Default values for development; fail fast on missing required config in production
5. Feature flags as configuration, not code branches — use a flag service or environment variables

### Security

**Principle:** Authentication at the edge, authorization close to the domain.

**Recommended approach:**
1. **Authentication (AuthN)** — Verify identity at the edge (middleware/gateway):
   - Validate tokens/sessions before requests reach controllers
   - Use established libraries — never implement crypto from scratch
2. **Authorization (AuthZ)** — Check permissions as close to the protected resource as appropriate:
   - Coarse-grained: middleware (e.g., "must be authenticated", "must have admin role")
   - Fine-grained: use case or domain service (e.g., "user can only edit their own orders")
3. **Input validation** — Validate at the boundary:
   - Syntactic validation (format, length, type) in the controller/adapter layer
   - Semantic validation (business rules) in the domain layer
4. **Output sanitization** — Never expose internal details:
   - Strip stack traces from production error responses
   - Use DTOs to control exactly what data leaves the system
5. **Principle of least privilege** — Grant the minimum access needed for each operation

### Caching

**Principle:** Cache at the boundary closest to the consumer. Introduce only when you have measured a performance problem.

**Recommended approach:**
1. **Cache-aside (lazy loading)** as the default pattern:
   - Check cache → if miss, load from source → store in cache → return
   - Simple, widely understood, works with any cache backend
2. **Cache placement** (closest to consumer first):
   - HTTP cache headers (browser/CDN) — for public, rarely-changing data
   - Application-level cache (in-memory or Redis) — for computed results, session data
   - Query-result cache — for expensive database queries
3. **Invalidation strategy:**
   - TTL-based expiration for most cases
   - Event-driven invalidation for data that must be fresh
   - Accept staleness where the business allows it
4. **Do not cache speculatively** — profile first, cache the proven bottleneck

---

## 5. Greenfield Decision Framework

Use this framework in Step 1 (Scope Assessment) to calibrate the depth and complexity of the design.

### Assessment Questions

Ask 2-3 of these questions based on what isn't already clear from the project context:

**Q1. Domain Complexity — What kind of business logic does this feature involve?**
- **(A) Simple CRUD** — Standard data entry/retrieval with minimal validation. Examples: user profiles, settings pages, basic catalogs.
- **(B) Moderate** — Business rules beyond basic CRUD. Workflow states, conditional logic, calculated fields. Examples: order processing, approval workflows, scheduling.
- **(C) Complex** — Rich domain with invariants, multi-step processes, domain events. Examples: financial transactions, logistics optimization, compliance engines.

**Q2. Team and Scale — What is the team and deployment context?**
- **(A) Solo/Small** — 1-3 developers, single deployment unit. Simplicity over flexibility.
- **(B) Medium** — 4-10 developers, may need clear module boundaries. Balance simplicity with maintainability.
- **(C) Large/Multiple teams** — 10+ developers or multiple teams. Strong boundaries, independent deployability, explicit contracts between modules.

**Q3. Testability — How important is testing isolation for this feature?**
- **(A) Standard** — Unit tests on business logic, integration tests on endpoints. Framework test utilities are acceptable.
- **(B) High** — Domain logic must be testable without any framework or infrastructure dependencies. Mocking at boundaries only.

### Scoring and Recommendation

Map the assessment to an architecture pattern:

| Q1 | Q2 | Q3 | Recommended Pattern |
|----|----|----|-------------------|
| A | A | A | Layered (simple N-Tier with DI) |
| A | B/C | Any | Layered with clear module boundaries |
| B | A/B | A | Clean Architecture (light) |
| B | Any | B | Clean Architecture |
| C | Any | Any | Hexagonal Architecture |

**When in doubt:** Clean Architecture is the safest default. It scales up to hexagonal with minimal refactoring and scales down to layered by relaxing boundaries.

### Project Structure Convention

Organize by feature/domain rather than by technical layer:

```
# Preferred: feature-oriented
src/
├── orders/
│   ├── domain/          # entities, value objects, repository interfaces
│   ├── application/     # use cases, application services
│   ├── adapters/        # controllers, DTOs, presenters
│   └── infrastructure/  # repository implementations, external clients
├── users/
│   ├── domain/
│   ├── application/
│   ├── adapters/
│   └── infrastructure/
└── shared/              # cross-cutting: middleware, config, common types

# Avoid: layer-oriented (becomes unwieldy as features grow)
src/
├── controllers/         # all controllers mixed together
├── services/            # all services mixed together
├── models/              # all models mixed together
└── repositories/        # all repositories mixed together
```

Feature-oriented structure scales with the domain — each feature is a self-contained module. Layer-oriented structure creates sprawling directories where related code is scattered across the tree.

### Monolith vs. Microservices

**Default: Start with a modular monolith.** Microservices are justified only when you have:
1. Proven CI/CD automation and deployment pipeline
2. Clear bounded-context boundaries validated by domain analysis
3. Team structure aligned to service ownership (Conway's Law)
4. Operational maturity for distributed systems (monitoring, tracing, incident response)

Successful microservice architectures typically evolve from monoliths. Greenfield microservices frequently fail due to premature distribution of a poorly understood domain.

**Build a modular monolith with explicit boundaries** — if you later need to extract a service, the boundaries are already defined and the extraction is mechanical.
