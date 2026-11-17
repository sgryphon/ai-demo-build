## General

- Make demos runnable unchanged in different subscriptions: default orgId deterministically from the subscription ID and provide repeatable network allocations when needed; allow explicit overrides.
- Document direct deployment commands; add wrapper scripts only when they provide meaningful value.
- Keep documentation concise: describe what is deployed and noteworthy constraints.
- Don't add bonus features without explicit request; stick to what's asked.
- When asked a question, answer the question; don't make changes.
- If something is unclear, ask to clarify; don't guess.

## Bicep

- Use IPv6-first networking, CIDR functions, and /64 IPv6 subnets.
- Put deployment assets in deployment/ within each project or sample.
- Keep baseline/ as the current desired state for fresh deployments; put explicit, ordered transitions for existing environments in migrations/ (only when requested).
- Use numbered stack folders under deployment/baseline/, each with main.bicep and sibling component modules.
- Keep modules one level deep; orchestrate component modules from the top level.
- Separate optional foundation initialization (RG, networking, monitoring) from workload deployment.
- Accept corporate-provided resource IDs and address allocations; don't assume subscription-level permissions.
- Follow CAF resource abbreviations and naming, with deterministic uniquifiers where needed.
- Tag all supported resources, including demos; use lowercase keys and consistent values.
- Prefer current, supported Azure resource models and APIs; justify preview dependencies.
- Run standalone `bicep format`, `bicep build`, and `bicep lint` on changed Bicep files; don't access Azure without explicit approval.

## Python

- Load configuration from files and environment variables; support CLI arguments as overrides.
- Set argparse parameter defaults in the parameter definition, not in runtime logic.
- Format with [Black](https://black.readthedocs.io/) using default settings.
