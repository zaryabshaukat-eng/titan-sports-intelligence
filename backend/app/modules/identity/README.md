# Identity Foundation

TITAN exposes one provider-neutral `IdentityProvider` contract. Its output is a normalized `Principal` with a subject, optional organization ID, provider name, and TITAN roles. Authorization derives stable permissions from those roles rather than trusting provider-specific claims throughout the application. The contract includes authentication, token validation, user/role/permission resolution, and local provider health.

For development and testing, `DevelopmentIdentityProvider` authenticates configured bearer credentials from `TITAN_DEVELOPMENT_IDENTITY_CREDENTIALS`:

```json
{
  "local-analyst-token": {
    "subject": "analyst@example.test",
    "organization_id": "development",
    "roles": ["analyst"]
  }
}
```

The default development credential is `titan-development-admin`; it must never be used outside local development. Production configuration rejects the development provider.

`JwtIdentityProvider` is a generic local HS256 validator. It verifies the compact token signature, issuer, audience, expiry, optional `nbf` claim, and configured clock skew before mapping `sub`, `organization_id`, and `roles` claims to a `Principal`. Configure it with `TITAN_IDENTITY_PROVIDER=jwt`, `TITAN_JWT_ISSUER`, `TITAN_JWT_AUDIENCE`, `TITAN_JWT_HS256_SECRET`, and optionally `TITAN_JWT_CLOCK_SKEW_SECONDS`. `TITAN_JWT_PUBLIC_KEY_PEM` is reserved for a future asymmetric-key implementation; no remote identity integration or OAuth flow is included.

Roles are `titan_admin`, `data_ingestor`, `analyst`, `operator`, `researcher`, and `viewer`. Permissions are an extensible application vocabulary, including data/sports/fixture/statistics/market reads, scoped ingestion operations, research execution, configuration/audit/identity administration, and outbox operation.

Authentication middleware validates a bearer token once, attaches the `Principal` to request state, and emits structured authentication audit logs. Permission dependencies use `require_permissions(...)`; route owners declare TITAN permissions only and never a concrete provider. Authentication and authorization logs include provider, subject where available, roles, effective permissions, endpoint/outcome, and the existing request/trace correlation IDs.
