# Compliance Roadmap

Enterprise-grade security foundations for B2B deployments. Target frameworks: HIPAA, SOC2 Type II, HITRUST CSF, FedRAMP, ISO 27001, PCI DSS.

**Design principle:** Security must not destroy developer experience. Dev mode stays easy; prod mode is strict. Features are on by default in production, optional and transparent in dev.

## Current Security Posture

**Exists:** JWT auth (HS256), app-to-app auth, household role model (MEMBER / POWER_USER / ADMIN), `is_superuser` flag, multi-tenant `household_id` isolation, centralized logging (Loki + Grafana), soft deletes, bcrypt passwords.

**Missing:** Audit trails, encryption in transit and at rest, RBAC enforcement, rate limiting, data classification, network hardening, log retention beyond 7 days.

## Phase Overview

| Phase | Area | Scope | Dependencies |
|-------|------|-------|--------------|
| 1 | Audit Logging | Events table, audit-client lib, account lockout | None |
| 2 | Encryption in Transit | TLS for PostgreSQL, Redis, MQTT, MinIO | None |
| 3 | Encryption at Rest | LUKS/FileVault, MinIO SSE, encrypted backups | Phase 2 |
| 4 | RBAC | Roles/permissions tables, enforcement middleware, JWT claims | Phase 1 |
| 5 | Rate Limiting + Sessions | slowapi middleware, session management, max concurrent sessions | Phase 1 |
| 6 | Data Classification + PII | Log sanitization, retention policies, right-to-deletion | Phase 1 |
| 7 | Network Hardening | Docker segmentation, CORS, security headers, MQTT ACLs | Phase 2 |
| 8 | Compliance Docs + Monitoring | Policy documents, Grafana dashboards, automated checks | All |

## Phase 1: Audit Logging Foundation

Every compliance framework requires provable audit trails. Without this, no other control is verifiable.

**Compliance:** ALL frameworks (SOC2, HIPAA, ISO 27001, FedRAMP, PCI DSS, HITRUST)

Tasks:

- **Audit events table** -- Append-only `audit_events` table in `jarvis-auth` with event type, actor, resource, action, details, source IP, household, and timestamp. DB user has INSERT only (no UPDATE/DELETE).
- **Audit client library** -- `jarvis-audit-client` following the `jarvis-log-client` pattern. Async batching, fire-and-forget, graceful degradation. Disabled via `AUDIT_ENABLED=false` for dev.
- **Instrument auth events** -- Login success/failure, registration, logout, token refresh, app-to-app and node validation.
- **Instrument data access** -- Memory CRUD, admin actions (node management, adapter training).
- **Account lockout** -- Lock account after 10 failed logins (15 min cooldown). Configurable via settings.
- **Audit query API** -- Admin-only endpoint for querying audit events with filters and pagination.

## Phase 2: Encryption in Transit (TLS)

All inter-service traffic is currently plaintext HTTP.

**Compliance:** HIPAA 164.312(e), PCI DSS Req 4, FedRAMP SC-8, ISO 27001 A.10.1

Tasks:

- **Auto-generated dev certificates** -- `./jarvis setup-certs` generates self-signed CA and per-service certs. Prod uses real certs or Let's Encrypt via Caddy.
- **PostgreSQL TLS** -- Mount certs, enable `ssl = on`, update DATABASE_URL with `sslmode=require` (prod) / `sslmode=prefer` (dev).
- **Redis TLS + auth** -- TLS listener, password authentication. Dev mode opt-out via `REDIS_TLS=false`.
- **MQTT TLS + auth** -- Mosquitto TLS on port 8883, password file, `allow_anonymous false`.
- **MinIO TLS** -- SSE-S3 enabled, certs mounted, strong credentials.
- **Port binding** -- Data stores bind to `127.0.0.1` only. Only the reverse proxy exposed on `0.0.0.0`.
- **Environment enforcement** -- `JARVIS_ENV=production` requires TLS or refuses to start.

## Phase 3: Encryption at Rest (AES-256)

**Compliance:** HIPAA 164.312(a)(2)(iv), PCI DSS Req 3, FedRAMP SC-28

Tasks:

- **Volume-level encryption** -- LUKS/dm-crypt on Linux host volumes. macOS already covered by FileVault.
- **MinIO SSE** -- Server-side encryption with AES-256 via `MINIO_KMS_SECRET_KEY`.
- **Encrypted backups** -- pg_dump output encrypted with GPG (AES-256).
- **Field-level encryption** (optional) -- AES-256-GCM for sensitive columns (user memories, emails). Searchable via blind index.

## Phase 4: RBAC (Role-Based Access Control)

**Compliance:** HIPAA 164.312(a)(1), SOC2 CC6.1, PCI DSS Req 7, FedRAMP AC-2/AC-3

Tasks:

- **Permission model** -- `roles`, `permissions`, `role_permissions`, `user_roles` tables in `jarvis-auth`.
- **Default roles** -- superadmin, household_admin, household_member, service_account, node.
- **Enforcement middleware** -- `@require_permission("resource", "action")` decorator. Checks JWT role claims (no extra DB lookup per request).
- **Migration** -- Convert `is_superuser` and `ADMIN_API_KEY` checks to role-based permissions. Add `roles` claim to JWT payload.
- **Admin API** -- CRUD for roles, permissions, and user-role assignments.

## Phase 5: Rate Limiting + Session Management

**Compliance:** SOC2 CC6.6, PCI DSS Req 8.1.6

Tasks:

- **Rate limiting** (slowapi) -- Auth endpoints: 10 req/min per IP. General API: 100 req/min. Admin: 30 req/min. Dev mode: 1000/min.
- **Session management** -- Max concurrent sessions per user (default 5), force-logout, session listing.

## Phase 6: Data Classification + PII Handling

**Compliance:** HIPAA PHI, SOC2 confidentiality, ISO 27001 A.8.2, GDPR-ready

Tasks:

- **Classification levels** -- PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED (PHI/PII).
- **PII inventory** -- Document which data falls into each category (emails: CONFIDENTIAL, memories: RESTRICTED, transcriptions: RESTRICTED).
- **Log sanitization** -- Middleware to redact RESTRICTED fields before logging.
- **Retention policies** -- Audit logs: 7 years. Operational logs: 90 days. Transcriptions: 30 days. User data: until deletion request.
- **Right-to-deletion** -- GDPR-ready endpoint to anonymize user data across services.

## Phase 7: Network Hardening

**Compliance:** PCI DSS Req 1-2, FedRAMP SC-7, ISO 27001 A.13

Tasks:

- **Docker network segmentation** -- Separate `jarvis-frontend`, `jarvis-backend`, and `jarvis-data` networks.
- **CORS hardening** -- Replace `allow_origins=["*"]` with explicit per-environment origins.
- **Security headers** -- HSTS, CSP, X-Frame-Options, X-Content-Type-Options. Remove server version headers.
- **MQTT ACLs** -- Restrict nodes to their own topics (`jarvis/node/{node_id}/#`).

## Phase 8: Compliance Documentation + Monitoring

**Compliance:** ALL (documentation requirements for certification)

Tasks:

- **Policy documents** -- Access Control, Encryption, Incident Response, Data Retention, Change Management.
- **Compliance matrix** -- Framework to control to implementation to evidence mapping.
- **Grafana dashboards** -- Failed logins, permission denials, audit event volume, service health. Alert rules for anomalies.
- **Automated checks** -- `scripts/compliance-check.sh` to verify TLS, encryption, audit, rate limiting, RBAC in CI/CD.
- **JWT upgrade path** -- HS256 to RS256 (asymmetric signing) for FedRAMP FIPS 140-2.

## Phase Dependencies

```
Phase 1 (Audit) ─────────┐
                          ├──> Phase 4 (RBAC)
Phase 2 (TLS) ──> Phase 3│
                          ├──> Phase 5 (Rate Limiting)
                          ├──> Phase 6 (Data Classification)
Phase 7 (Network) <── Phase 2
                          │
Phase 8 (Docs) <── ALL ──┘
```

Phases 1 and 2 can run in parallel. Everything else depends on at least one of them.
