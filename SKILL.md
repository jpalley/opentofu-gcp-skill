---
name: opentofu-skill-gcp
description: Use when working with OpenTofu for GCP - creating modules, writing tests (native test framework, Terratest), setting up CI/CD pipelines with Cloud Build, reviewing configurations, state encryption with GCP KMS, debugging state issues, implementing security scanning (trivy, checkov, prowler), or making infrastructure-as-code architecture decisions for Google Cloud Platform
---

# OpenTofu Skill for GCP

Comprehensive OpenTofu guidance for Google Cloud Platform covering state encryption, testing, modules, CI/CD with Cloud Build, and production patterns. Based on terraform-best-practices.com and enterprise GCP experience.

## When to Use This Skill

**Activate this skill when:**
- Creating new OpenTofu configurations or modules for GCP
- Setting up testing infrastructure for IaC code
- Configuring state encryption with GCP KMS
- Deciding between testing approaches (validate, plan, frameworks)
- Structuring multi-environment GCP deployments
- Implementing CI/CD with Cloud Build or GitHub Actions
- Reviewing or refactoring existing OpenTofu/GCP projects
- Setting up Workload Identity Federation for CI/CD

**Don't use this skill for:**
- Basic OpenTofu syntax questions (Claude knows this)
- Provider-specific API reference (link to docs instead)
- Non-GCP cloud platform questions

## OpenTofu-Unique Features

OpenTofu provides capabilities beyond Terraform. Use these features for enhanced security and flexibility.

### State Encryption (OpenTofu 1.7+)

**Client-side encryption with GCP KMS:**

```hcl
tofu {
  encryption {
    method "gcp_kms" "state_key" {
      kms_encryption_key = "projects/my-project/locations/global/keyRings/tofu-state/cryptoKeys/state-key"
    }
    state {
      method = method.gcp_kms.state_key
    }
    plan {
      method = method.gcp_kms.state_key
    }
  }

  backend "gcs" {
    bucket = "my-tofu-state"
    prefix = "prod"
  }
}
```

### Early Variable Evaluation (OpenTofu 1.8+)

**Use variables in backend and module source:**

```hcl
variable "environment" {
  type = string
}

tofu {
  backend "gcs" {
    bucket = "tofu-state-${var.environment}"
    prefix = var.environment
  }
}
```

### Enabled Meta-Argument (OpenTofu 1.11+)

**Cleaner conditional resource creation:**

```hcl
# ✅ GOOD - enabled meta-argument (OpenTofu 1.11+)
resource "google_compute_instance" "bastion" {
  enabled = var.create_bastion

  name         = "bastion-host"
  machine_type = "e2-micro"
  zone         = var.zone
}

# Instead of count = var.create_bastion ? 1 : 0
```

### Ephemeral Resources (OpenTofu 1.11+)

**Secrets that never touch state:**

```hcl
ephemeral "google_secret_manager_secret_version" "db_password" {
  secret = "projects/my-project/secrets/db-password"
}

resource "google_sql_database_instance" "main" {
  name             = "main-instance"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"
  }

  # Ephemeral value - never stored in state
  root_password = ephemeral.google_secret_manager_secret_version.db_password.secret_data
}
```

## Core Principles

### 1. Code Structure Philosophy

**Module Hierarchy:**

| Type | When to Use | Scope |
|------|-------------|-------|
| **Resource Module** | Single logical group of connected resources | VPC + subnets, Firewall + rules |
| **Infrastructure Module** | Collection of resource modules for a purpose | Multiple resource modules in one region/project |
| **Composition** | Complete infrastructure | Spans multiple regions/projects |

**Hierarchy:** Resource → Resource Module → Infrastructure Module → Composition

**Directory Structure:**
```
environments/        # Environment-specific configurations
├── prod/
├── staging/
└── dev/

modules/            # Reusable modules
├── networking/
├── compute/
├── gke/
└── data/

examples/           # Module usage examples (also serve as tests)
├── complete/
└── minimal/
```

**Key principle from terraform-best-practices.com:**
- Separate **environments** (prod, staging) from **modules** (reusable components)
- Use **examples/** as both documentation and integration test fixtures
- Keep modules small and focused (single responsibility)

**For detailed module architecture, see:** [Code Patterns: Module Types & Hierarchy](references/code-patterns.md)

### 2. Naming Conventions

**Resources:**
```hcl
# Good: Descriptive, contextual (GCP uses hyphens in resource names)
resource "google_compute_instance" "web-server" { }
resource "google_storage_bucket" "application-logs" { }

# Good: "this" for singleton resources (only one of that type)
resource "google_compute_network" "this" { }
resource "google_compute_firewall" "this" { }

# Avoid: Generic names for non-singletons
resource "google_compute_instance" "main" { }
resource "google_storage_bucket" "bucket" { }
```

**GCP Naming Note:** GCP resource names use hyphens (kebab-case), but HCL identifiers use underscores (snake_case).

**Singleton Resources:**

Use `"this"` when your module creates only one resource of that type:

✅ DO:
```hcl
resource "google_compute_network" "this" {}           # Module creates one VPC
resource "google_compute_firewall" "this" {}          # Module creates one firewall
```

❌ DON'T use "this" for multiple resources:
```hcl
resource "google_compute_subnetwork" "this" {}  # If creating multiple subnets
```

Use descriptive names when creating multiple resources of the same type.

**Variables:**
```hcl
# Prefix with context when needed
var.vpc_cidr_range              # Not just "cidr"
var.database_tier               # Not just "tier"
```

**Files:**
- `main.tf` - Primary resources
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `versions.tf` - Provider versions
- `data.tf` - Data sources (optional)

## Testing Strategy Framework

### Decision Matrix: Which Testing Approach?

| Your Situation | Recommended Approach | Tools | Cost |
|----------------|---------------------|-------|------|
| **Quick syntax check** | Static analysis | `tofu validate`, `fmt` | Free |
| **Pre-commit validation** | Static + lint | `validate`, `tflint`, `trivy`, `checkov` | Free |
| **OpenTofu 1.6+, simple logic** | Native test framework | Built-in `tofu test` | Free-Low |
| **Go expertise** | Integration testing | Terratest | Low-Med |
| **Security/compliance focus** | Policy as code | OPA, Checkov | Free |
| **Cost-sensitive workflow** | Mock providers (1.7+) | Native tests + mocking | Free |
| **Multi-service, complex** | Full integration | Terratest + real infra | Med-High |

### Testing Pyramid for Infrastructure

```
        /\
       /  \          End-to-End Tests (Expensive)
      /____\         - Full environment deployment
     /      \        - Production-like setup
    /________\
   /          \      Integration Tests (Moderate)
  /____________\     - Module testing in isolation
 /              \    - Real resources in test project
/________________\   Static Analysis (Cheap)
                     - validate, fmt, lint
                     - Security scanning (trivy, checkov)
```

### Native Test Best Practices (1.6+)

**Before generating test code:**

1. **Validate schemas with provider docs:**
   ```
   Search provider docs → Get resource schema → Identify block types
   ```

2. **Choose correct command mode:**
   - `command = plan` - Fast, for input validation
   - `command = apply` - Required for computed values and set-type blocks

3. **Handle set-type blocks correctly:**
   - Cannot index with `[0]`
   - Use `for` expressions to iterate
   - Or use `command = apply` to materialize

**For detailed testing guides, see:**
- **[Testing Frameworks Guide](references/testing-frameworks.md)** - Deep dive into static analysis, native tests, and Terratest
- **[Quick Reference](references/quick-reference.md#testing-approach-selection)** - Decision flowchart and command cheat sheet

## Code Structure Standards

### Resource Block Ordering

**Strict ordering for consistency:**
1. `count` or `for_each` or `enabled` FIRST (blank line after)
2. Other arguments
3. `labels` as last real argument (GCP uses labels, not tags)
4. `depends_on` after labels (if needed)
5. `lifecycle` at the very end (if needed)

```hcl
# ✅ GOOD - Correct ordering
resource "google_compute_router_nat" "this" {
  enabled = var.create_nat

  name                               = "${var.name}-nat"
  router                             = google_compute_router.this.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  depends_on = [google_compute_router.this]

  lifecycle {
    create_before_destroy = true
  }
}
```

### Variable Block Ordering

1. `description` (ALWAYS required)
2. `type`
3. `default`
4. `validation`
5. `nullable` (when setting to false)

```hcl
variable "environment" {
  description = "Environment name for resource labeling"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }

  nullable = false
}
```

**For complete structure guidelines, see:** [Code Patterns: Block Ordering & Structure](references/code-patterns.md#block-ordering--structure)

## Count vs For_Each: When to Use Each

### Quick Decision Guide

| Scenario | Use | Why |
|----------|-----|-----|
| Boolean condition (create or don't) | `enabled` (1.11+) or `count = condition ? 1 : 0` | Simple on/off toggle |
| Simple numeric replication | `count = 3` | Fixed number of identical resources |
| Items may be reordered/removed | `for_each = toset(list)` | Stable resource addresses |
| Reference by key | `for_each = map` | Named access to resources |
| Multiple named resources | `for_each` | Better maintainability |

### Common Patterns

**Boolean conditions:**
```hcl
# ✅ BEST - enabled meta-argument (OpenTofu 1.11+)
resource "google_compute_router_nat" "this" {
  enabled = var.create_nat
  # ...
}

# ✅ GOOD - Boolean condition (pre-1.11)
resource "google_compute_router_nat" "this" {
  count = var.create_nat ? 1 : 0
  # ...
}
```

**Stable addressing with for_each:**
```hcl
# ✅ GOOD - Removing "us-central1-b" only affects that subnet
resource "google_compute_subnetwork" "private" {
  for_each = toset(var.zones)

  name   = "private-${each.key}"
  region = var.region
  # ...
}

# ❌ BAD - Removing middle zone recreates all subsequent subnets
resource "google_compute_subnetwork" "private" {
  count = length(var.zones)

  name = "private-${var.zones[count.index]}"
  # ...
}
```

**For migration guides and detailed examples, see:** [Code Patterns: Count vs For_Each](references/code-patterns.md#count-vs-for_each-deep-dive)

## GCP Required Labels

**Always apply required labels to all resources:**

```hcl
locals {
  required_labels = {
    environment = var.environment      # dev, staging, prod
    project     = var.project_name     # application/service name
    managed-by  = "opentofu"           # always "opentofu"
    owner       = var.owner            # team or individual
    cost-center = var.cost_center      # billing allocation
  }
}

resource "google_compute_instance" "web-server" {
  name         = "web-server"
  machine_type = "e2-medium"
  zone         = var.zone

  # ... other config ...

  labels = local.required_labels
}
```

**For detailed conventions, see:** [Conventions Reference](references/conventions.md)

## Module Development

### Standard Module Structure

```
my-module/
├── README.md           # Usage documentation
├── main.tf             # Primary resources
├── variables.tf        # Input variables with descriptions
├── outputs.tf          # Output values
├── versions.tf         # Provider version constraints
├── examples/
│   ├── minimal/        # Minimal working example
│   └── complete/       # Full-featured example
└── tests/              # Test files
    └── module_test.tftest.hcl  # Or .go
```

### Module Naming Convention

```
tofu-google-<NAME>

Examples:
tofu-google-vpc
tofu-google-gke
tofu-google-cloudsql
```

### Best Practices Summary

**Variables:**
- ✅ Always include `description`
- ✅ Use explicit `type` constraints
- ✅ Provide sensible `default` values where appropriate
- ✅ Add `validation` blocks for complex constraints
- ✅ Use `sensitive = true` for secrets

**Outputs:**
- ✅ Always include `description`
- ✅ Mark sensitive outputs with `sensitive = true`
- ✅ Consider returning objects for related values
- ✅ Document what consumers should do with each output

**For detailed module patterns, see:**
- **[Module Patterns Guide](references/module-patterns.md)** - Variable best practices, output design, ✅ DO vs ❌ DON'T patterns
- **[Quick Reference](references/quick-reference.md#common-patterns)** - Resource naming, variable naming, file organization

## CI/CD Integration

### Recommended Workflow Stages

1. **Validate** - Format check + syntax validation + linting
2. **Security Scan** - Trivy + Checkov for IaC scanning
3. **Test** - Run automated tests (native or Terratest)
4. **Plan** - Generate and review execution plan
5. **Apply** - Execute changes (with approvals for production)

### Cost Optimization Strategy

1. **Use mocking for PR validation** (free)
2. **Run integration tests only on main branch** (controlled cost)
3. **Implement auto-cleanup** (prevent orphaned resources)
4. **Label all test resources** (track spending)

**For complete CI/CD templates, see:**
- **[CI/CD Workflows Guide](references/ci-cd-workflows.md)** - Cloud Build, GitHub Actions with Workload Identity Federation
- **[Quick Reference](references/quick-reference.md#troubleshooting-guide)** - Common CI/CD issues and solutions

## Security & Compliance

### Essential Security Checks

```bash
# Static security scanning (IaC)
trivy config . --severity CRITICAL,HIGH
checkov -d . --framework terraform

# Scan plan file before apply
tofu plan -out=tfplan
tofu show -json tfplan > tfplan.json
checkov -f tfplan.json

# Cloud posture assessment (post-deploy)
prowler gcp --project-id my-project
```

### Three-Tier Security Scanning

| Tool | Type | GCP Checks | When to Use |
|------|------|-----------|-------------|
| **Trivy** | IaC static analysis | AVD-GCP-* checks | Pre-commit, CI/CD - scan code before apply |
| **Checkov** | IaC policy scanner | CKV_GCP_* checks | CI/CD - policy compliance, graph analysis |
| **Prowler** | Cloud posture | 100+ GCP controls | Post-deploy - audit deployed infrastructure |

### Common Issues to Avoid

❌ **Don't:**
- Store secrets in variables
- Use default networks
- Skip encryption
- Open firewall rules to 0.0.0.0/0
- Use primitive IAM roles (Owner, Editor, Viewer)

✅ **Do:**
- Use Google Secret Manager
- Create dedicated VPC networks
- Enable encryption at rest (CMEK where required)
- Use least-privilege firewall rules
- Use predefined IAM roles

**For detailed security guidance, see:**
- **[Security & Compliance Guide](references/security-compliance.md)** - Trivy/Checkov/Prowler integration, secrets management, state encryption

## Version Management

### Version Constraint Syntax

```hcl
version = "5.0.0"      # Exact (avoid - inflexible)
version = "~> 5.0"     # Recommended: 5.0.x only
version = ">= 5.0"     # Minimum (risky - breaking changes)
```

### Strategy by Component

| Component | Strategy | Example |
|-----------|----------|---------|
| **OpenTofu** | Pin minor version | `required_version = "~> 1.11"` |
| **Providers** | Pin major version | `version = "~> 6.0"` |
| **Modules (prod)** | Pin exact version | `version = "5.1.2"` |
| **Modules (dev)** | Allow patch updates | `version = "~> 5.1"` |

### Update Workflow

```bash
# Lock versions initially
tofu init              # Creates .terraform.lock.hcl

# Update to latest within constraints
tofu init -upgrade     # Updates providers

# Review and test
tofu plan
```

**For detailed version management, see:** [Code Patterns: Version Management](references/code-patterns.md#version-management)

## OpenTofu Version Features

### Feature Availability by Version

| Feature | Version | Use Case |
|---------|---------|----------|
| `try()` function | 1.0+ | Safe fallbacks |
| `nullable = false` | 1.1+ | Prevent null values in variables |
| `moved` blocks | 1.1+ | Refactor without destroy/recreate |
| `optional()` with defaults | 1.3+ | Optional object attributes |
| Native testing | 1.6+ | Built-in test framework |
| Mock providers | 1.7+ | Cost-free unit testing |
| **State encryption** | 1.7+ | Client-side encryption with GCP KMS |
| **Early variable evaluation** | 1.8+ | Variables in backend/module source |
| Cross-variable validation | 1.9+ | Validate relationships between variables |
| **`enabled` meta-argument** | 1.11+ | Cleaner conditional resources |
| **Ephemeral resources** | 1.11+ | Secrets never stored in state |

### Quick Examples

```hcl
# try() - Safe fallbacks (1.0+)
output "instance_id" {
  value = try(google_compute_instance.this[0].id, "")
}

# optional() - Optional attributes with defaults (1.3+)
variable "config" {
  type = object({
    name    = string
    timeout = optional(number, 300)  # Default: 300
  })
}

# Cross-variable validation (1.9+)
variable "environment" { type = string }
variable "backup_days" {
  type = number
  validation {
    condition     = var.environment == "prod" ? var.backup_days >= 7 : true
    error_message = "Production requires backup_days >= 7"
  }
}
```

**For complete patterns and examples, see:** [Code Patterns: Modern OpenTofu Features](references/code-patterns.md#modern-terraform-features-10)

## Additional Resources

**Official:** [OpenTofu Docs](https://opentofu.org/docs/) | [OpenTofu Testing](https://opentofu.org/docs/language/tests/) | [Google Cloud Best Practices](https://cloud.google.com/docs/terraform/best-practices)

**Community:** [terraform-best-practices.com](https://terraform-best-practices.com) | [Terratest](https://terratest.gruntwork.io/docs/)

**Tools:** [pre-commit-terraform](https://github.com/antonbabenko/pre-commit-terraform) | [terraform-docs](https://terraform-docs.io/) | [TFLint](https://github.com/terraform-linters/tflint) | [Trivy](https://github.com/aquasecurity/trivy) | [Checkov](https://www.checkov.io/) | [Prowler](https://github.com/prowler-cloud/prowler)

**Ecosystem:**
- [Terragrunt](https://terragrunt.gruntwork.io/) - Orchestration tool for DRY configurations
- [Atlantis](https://www.runatlantis.io/) - Pull Request automation
- [Infracost](https://www.infracost.io/) - Cloud cost estimates in PRs
- [tofuenv](https://github.com/tofuutils/tofuenv) - OpenTofu version manager

## Detailed Guides

This skill uses **progressive disclosure** - essential information is in this main file, detailed guides are available when needed:

📚 **Reference Files:**
- **[Testing Frameworks](references/testing-frameworks.md)** - In-depth guide to static analysis, native tests, and Terratest
- **[Module Patterns](references/module-patterns.md)** - Module structure, variable/output best practices, ✅ DO vs ❌ DON'T patterns
- **[CI/CD Workflows](references/ci-cd-workflows.md)** - Cloud Build, GitHub Actions with Workload Identity Federation
- **[Security & Compliance](references/security-compliance.md)** - Trivy/Checkov/Prowler integration, secrets management, state encryption
- **[Quick Reference](references/quick-reference.md)** - Command cheat sheets, decision flowcharts, troubleshooting guide
- **[Conventions](references/conventions.md)** - Required GCP labels, naming conventions, organization templates
- **[Code Patterns](references/code-patterns.md)** - Block ordering, count vs for_each, modern OpenTofu features

**How to use:** When you need detailed information on a topic, reference the appropriate guide. Claude will load it on demand to provide comprehensive guidance.

## License & Attribution

This skill is licensed under the **Apache License 2.0**. See the LICENSE file for full terms.

**Copyright © 2026 Anton Babenko**

### Sources

This skill synthesizes best practices from:
- **[terraform-best-practices.com](https://terraform-best-practices.com)** by Anton Babenko
- **[Compliance.tf](https://compliance.tf)** - OpenTofu Compliance for Cloud-Native Enterprise (production experience)
- Official OpenTofu documentation
- Google Cloud Terraform/OpenTofu Best Practices
- Community contributions

### Attribution

If you create derivative works or skills based on this skill, please include:
```
Based on opentofu-skill-gcp by Anton Babenko
https://github.com/antonbabenko/terraform-skill
terraform-best-practices.com | Compliance.tf
```

### About the author

Anton Babenko ([@antonbabenko on X](https://x.com/antonbabenko)) is an AWS Hero and the creator of [terraform-best-practices.com](https://terraform-best-practices.com). Anton is the founder of [Compliance.tf](https://compliance.tf), which helps teams build compliant OpenTofu for cloud-native enterprises. Anton also curates [weekly.tf](https://weekly.tf), the Terraform Weekly newsletter, and maintains the [terraform-aws-modules](https://github.com/terraform-aws-modules) project.
