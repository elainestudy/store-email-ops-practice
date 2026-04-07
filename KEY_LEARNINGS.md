# Store Email Ops - Key Learnings

After completing this project, you should understand these core concepts and be able to explain them in interviews.

This guide captures the essential takeaways about building production-ready email systems with async workflows.

## Prep Priorities

Focus on these areas first:

1. Project architecture
2. Data model
3. Testing strategy
4. AWS design
5. Security
6. Terraform
7. Resume alignment

## 1. Project Architecture

### Q: What is the core workflow of this internal email tool?

A:
Store users create and manage email campaigns through an internal UI. The Flask API validates the request, stores campaign and recipient data in a relational database, and publishes a send job to a queue. A worker or Lambda consumes the message asynchronously, sends emails, records delivery attempts, and updates campaign status for later auditing and support.

Short answer:
It is an internal email operations workflow where the API persists campaign data, queues sending work, and background workers process delivery asynchronously while storing audit and delivery history.

### Q: Why not send emails synchronously inside the API request?

A:
Sending email directly inside the request path makes the API slower, less reliable, and harder to scale. Email delivery depends on external systems and can fail or time out. By using asynchronous processing, the API can return quickly while background workers handle retries, failure logging, and delivery tracking more safely.

### Q: Why use a queue and async processing?

A:
A queue decouples campaign creation from email delivery. It improves reliability, supports retries, smooths traffic spikes, and prevents one slow downstream dependency from blocking the user-facing API. It also makes it easier to scale workers independently from the API layer.

### Q: What parts are already implemented in this local practice project?

A:
The local project includes a Flask API, relational persistence with SQLite and SQLModel, a send queue abstraction, a worker flow that processes queued send requests, recipient records, delivery attempt records, and audit logs. The local default queue backend is in-memory for fast testing, and a Kafka producer backend is also included to demonstrate how the async boundary can map to a real queueing system.

### Q: Why is a relational database a good fit here?

A:
This domain has strongly related business entities such as campaigns, recipients, delivery attempts, and audit records. Relational databases are a good fit because they support joins, filtering, reporting, and transactional consistency well. That makes them a practical source of truth for internal tools and operational workflows.

## 2. Data Model

### Q: What tables would you expect in this system?

A:
At minimum I would model `campaign`, `recipient`, `delivery_attempt`, and `audit_log`. Depending on scope, I might also add `store`, `customer_segment`, or `campaign_recipient` if recipients are selected dynamically.

Short answer:
The four core tables are `campaign`, `recipient`, `delivery_attempt`, and `audit_log`. Together they cover campaign definition, target recipients, operational send outcomes, and traceability.

### Q: What does the `campaign` table store?

A:
It stores campaign-level metadata such as campaign id, name, subject, body template, store id, status, created timestamp, and possibly scheduling information.

Short answer:
`campaign` stores the campaign definition and lifecycle state, such as subject, body, store ownership, status, and timestamps.

### Q: What does the `recipient` table store?

A:
It stores recipient-level information such as recipient id, campaign id, customer email, customer identifier, personalization fields, and current delivery status.

Short answer:
`recipient` stores who should receive a campaign and the current per-recipient delivery state.

### Q: What does the `delivery_attempt` table store?

A:
It stores operational delivery records such as attempt id, recipient id, provider response, send timestamp, retry count, final status, and error details if delivery failed.

Short answer:
`delivery_attempt` stores what happened each time the system tried to send an email, including timestamps, provider responses, retry count, and success or failure.

### Q: What does the `audit_log` table store?

A:
It stores system and operator actions for traceability, such as campaign creation, campaign approval, send trigger events, retries, and administrative changes.

Short answer:
`audit_log` stores important business and operational events so the team can trace who did what and what the system did in response.

### Q: Why separate `recipient`, `delivery_attempt`, and `audit_log` instead of storing everything on the campaign row?

A:
Those tables represent different levels of granularity. `campaign` is the aggregate definition, `recipient` is the per-customer target record, `delivery_attempt` is the per-send operational record, and `audit_log` is the traceability record. Separating them supports better reporting, retries, debugging, and historical analysis.

Short answer:
They capture different concerns at different levels. Keeping them separate makes querying, retries, auditing, and troubleshooting much cleaner.

## 3. Testing Strategy

### Q: How would you test this system?

A:
I would use a layered strategy. Unit tests would focus on business logic in services. Integration tests would exercise the Flask API with the database. BDD-style tests would cover end-to-end workflows such as creating a campaign, enqueueing sends, and observing delivery results.

Short answer:
I would use layered testing: unit tests for service logic, integration tests for API plus database behavior, and BDD-style tests for end-to-end business workflows.

### Q: What should unit tests cover?

A:
Unit tests should cover pure business logic such as validation rules, state transitions, id conversion, retry decisions, and idempotency behavior where possible.

Short answer:
Unit tests should focus on service logic and business rules without depending on the whole application stack.

### Q: What should integration tests cover?

A:
Integration tests should cover HTTP routes, request validation, database persistence, and error responses. They help verify that the route, schema, service, and data layers work together correctly.

Short answer:
Integration tests verify that the API, validation, database, and error handling work together correctly.

### Q: What is an example of a BDD-style scenario here?

A:
Given a valid campaign request, when a store user creates a campaign and triggers sending, then the system should persist the campaign, enqueue delivery work, and eventually record delivery outcomes for recipients.

Short answer:
For example: Given a valid campaign, when a store user triggers sending, then the system should queue work, process recipients, and record delivery results.

### Q: What does BDD-style mean?

A:
BDD stands for Behavior-Driven Development. In practice, BDD-style tests describe system behavior in business language, often using a `Given / When / Then` structure. The goal is to validate user-visible workflows rather than just isolated methods.

Short answer:
BDD-style means testing behavior from a business workflow perspective, usually with a `Given / When / Then` structure.

### Q: What can a BDD-style test look like in Python?

A:
It does not require special syntax. It can simply be written as a normal pytest test with comments or helper function names that reflect `Given / When / Then`. The important part is the business-oriented structure of the scenario.

Short answer:
In Python, BDD-style tests are often just normal pytest tests written in a `Given / When / Then` style.

### Q: Do integration tests include the database?

A:
Yes, ideally they do. Integration tests are most useful when they verify real collaboration between application layers such as the API, validation, and persistence. In this project, testing against a lightweight local database is more valuable than mocking persistence for every scenario.

Short answer:
Yes. Integration tests should usually include the real database layer or a realistic test database.

### Q: What about coverage expectations?

A:
Coverage is a useful signal, but it should not be the only quality metric. In many teams, coverage thresholds are enforced in CI, often with tools like pytest-cov, SonarQube, or similar dashboards. The important point is that high-risk business paths should be covered, not just that a percentage target is reached mechanically.

Short answer:
Coverage matters, but meaningful coverage matters more than hitting a number mechanically.

## 4. AWS Design

### Q: What AWS architecture would you propose for this project?

A:
I would use Flask for the API layer, RDS for relational business data, SQS for asynchronous job delivery, Lambda or workers for send processing, DynamoDB for idempotency or lightweight event state, Secrets Manager for credentials, and CloudWatch for logs and observability.

### Q: Where does SQS fit?

A:
SQS sits between the API and the email sending worker. The API writes a message when a send job is created, and workers consume messages independently. That separation improves resilience and scalability.

### Q: Why use DynamoDB if RDS already exists?

A:
DynamoDB is useful for specific access patterns such as idempotency keys, event state, or fast key-value lookups. RDS remains the source of truth for relational business data, while DynamoDB supports selected operational patterns efficiently.

Examples in this system:

- Idempotency keys for send requests, to avoid duplicate sends during retries
- Deduplication records for asynchronously consumed queue messages
- Lightweight event processing state such as `queued`, `processing`, `completed`, or `failed`
- Fast key-based operational lookups, for example a quick per-campaign async status summary

Short answer:
I would use DynamoDB for idempotency keys, async deduplication, and lightweight event state, while keeping relational business records in RDS.

### Q: What would Lambda do in this design?

A:
Lambda can consume SQS messages, send emails or call an email provider, update delivery status, and write operational events. It is a good fit for event-driven background processing.

### Q: How would you think about multi-region?

A:
I would start with one primary region and design for future failover. I would think about which parts need active-active behavior and which can be warm standby. I would also consider data consistency, replication lag, queue behavior, failover procedures, and the operational cost of true multi-region support.

### Q: Should send-related actions be recorded in an audit trail?

A:
Yes. Important send-related actions should be recorded for traceability, such as campaign creation, queueing, asynchronous processing, retries, failures, and administrative actions. In this system, I would usually keep the main audit trail in the relational database because internal tools often need filtering, reporting, and operational investigation across related entities.

Short answer:
Yes. Send-related actions should be audited, and in this system I would usually keep the main audit trail in the relational database.

## 5. Security

### Q: What security concerns matter for this project?

A:
The key concerns are secrets management, credential hygiene, least-privilege access, safe logging, input validation, and secure runtime configuration.

### Q: How would you manage secrets?

A:
I would avoid hardcoding secrets in code or images. In AWS I would use Secrets Manager or Parameter Store. Locally I would use environment variables or a `.env` file that is not committed.

### Q: What is credential hygiene?

A:
It means keeping credentials out of source control, rotating them when needed, limiting who can access them, and avoiding accidental exposure in logs, screenshots, or local scripts.

### Q: Why mention non-root containers?

A:
Running containers as non-root reduces blast radius if the container is compromised. It is a simple but important defense-in-depth practice.

### Q: What does least privilege IAM mean here?

A:
Each service should get only the permissions it actually needs. For example, the API might write to SQS and read secrets, while a worker might consume SQS messages and update database-related resources. Broad wildcard permissions should be avoided.

## 6. Terraform

### Q: What Terraform concepts should you be comfortable with?

A:
At minimum: resources, modules, variables, outputs, and environment-specific configuration.

### Q: What would Terraform manage in this project?

A:
It could provision the API-related infrastructure, SQS queues, Lambda functions, IAM roles and policies, security groups, secrets references, and RDS-related resources.

### Q: Why use modules?

A:
Modules help keep infrastructure reusable and organized. For example, I could separate networking, API, queueing, and data storage into smaller building blocks.

### Q: What are variables and outputs for?

A:
Variables let me parameterize environments such as dev and prod. Outputs let one part of the infrastructure expose useful values such as queue URLs, Lambda ARNs, or database endpoints to other parts.

## 7. Interview Story

### Q: How would you summarize this project in one sentence?

A:
It is an internal email operations tool where a Flask API manages campaigns, a relational database stores operational data, and asynchronous workers process delivery safely and scalably.

### Q: What are the most important engineering decisions in this project?

A:
Using async processing instead of synchronous delivery, choosing a relational source of truth for operational data, separating validation from business logic, and designing with security and cloud deployment in mind.

### Q: What would you say if asked why you used SQLite locally?

A:
I used SQLite locally to move faster while learning and prototyping the application flow. For a production-style deployment, I would target RDS with a relational engine such as PostgreSQL.
