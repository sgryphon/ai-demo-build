* Use modern networking and development.
* Use IPv6-first design.
* IPv6 addressing is effectively unlimited; use the standards.
* Don't do it the old standard way; do it the modern, best practice way.
* Put Bicep in infrastructure/ within each project or sample.
* Follow Azure naming conventions, with deterministic uniquifiers where needed.
* Tag all resources that support tags, including in demos.
* Separate optional RG/network initialization from workload deployment.
* Accept corporate-provided resource IDs and address allocations; don't assume subscription-level permissions.
* Use CIDR functions for subnet calculations; use /64 for IPv6 subnets.
* Support fresh deployment from the current model; use explicit migrations for transitions that require them.