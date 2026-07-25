# Identity Foundation

TITAN exposes one provider-neutral `IdentityProvider` contract. Its output is a normalized `Principal` with a subject, optional organization ID, and TITAN roles. Authorization derives stable permissions from those roles rather than trusting provider-specific claims throughout the application.

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

Current roles are `titan_admin`, `data_ingestor`, `analyst`, and `operator`. Current permissions cover data reads, fixture/market/statistics ingestion, and future outbox operations. New OAuth, SSO, service-account, or API-key providers implement only `IdentityProvider.authenticate` and are selected at application composition.
