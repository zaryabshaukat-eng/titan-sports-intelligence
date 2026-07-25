# Identity Foundation

Authentication is separated from authorization. `IdentityProvider` adapters authenticate a bearer credential and normalize it into a TITAN `Principal`. Authorization maps TITAN roles to stable permissions, so APIs do not depend on provider-specific claim names.

`AuthenticationMiddleware` validates supplied bearer credentials once per request and stores the verified principal in request state. FastAPI permission dependencies then protect routes and preserve OpenAPI bearer documentation.

The initial provider is development-only and uses configurable credentials. It is deliberately not OAuth and does not provide login flows. Production rejects the development provider, leaving the composition point ready for a future SSO, OAuth, or service-account adapter.
