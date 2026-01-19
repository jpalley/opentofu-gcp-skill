# OpenTofu Skill for GCP

[![Claude Skill](https://img.shields.io/badge/Claude-Skill-5865F2)](https://docs.claude.ai/docs/agent-skills)
[![OpenTofu](https://img.shields.io/badge/OpenTofu-1.11+-FFD814)](https://opentofu.org/)
[![GCP](https://img.shields.io/badge/GCP-Google%20Cloud-4285F4)](https://cloud.google.com/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Comprehensive OpenTofu best practices skill for Claude Code, optimized for Google Cloud Platform. Get instant guidance on testing strategies, module patterns, CI/CD workflows, security scanning, and production-ready GCP infrastructure code.

## What This Skill Provides

**OpenTofu-Unique Features**
- State encryption with GCP KMS (OpenTofu 1.7+)
- Early variable evaluation (OpenTofu 1.8+)
- `enabled` meta-argument (OpenTofu 1.11+)
- Ephemeral resources for secrets (OpenTofu 1.11+)

**Testing Frameworks**
- Decision matrix for native tests vs Terratest
- Testing strategy workflows (static → integration → E2E)
- GCP-specific test patterns (GKE, Cloud SQL, Pub/Sub)

**Module Development**
- Structure and naming conventions (`tofu-google-<NAME>`)
- GCP module patterns (VPC, GKE, Cloud SQL, Pub/Sub)
- Versioning strategies with semantic versioning

**CI/CD Integration**
- Cloud Build pipeline templates with security scanning
- GitHub Actions with Workload Identity Federation
- GitLab CI templates for GCP

**Security & Compliance**
- Three-tier scanning: Trivy (AVD-GCP-*), Checkov (CKV_GCP_*), Prowler
- State encryption configuration
- Google Secret Manager integration
- VPC Service Controls patterns

**Quick Reference**
- Decision flowcharts
- Common patterns (DO vs DON'T)
- GCP-specific cheat sheets

## Installation

This plugin is distributed via Claude Code marketplace using `.claude-plugin/marketplace.json`.

### Claude Code (Recommended)

```bash
/plugin install opentofu-skill-gcp
```

### Manual Installation

```bash
# Clone to Claude skills directory
git clone https://github.com/antonbabenko/opentofu-skill-gcp ~/.claude/skills/opentofu-skill-gcp
```

### Verify Installation

After installation, try:
```
"Create an OpenTofu module for a GCP VPC with tests"
```

Claude will automatically use the skill when working with OpenTofu/GCP code.

## Quick Start Examples

**Create a module with tests:**
> "Create an OpenTofu module for GCP VPC with native tests"

**Set up state encryption:**
> "Configure state encryption with GCP KMS for OpenTofu"

**Review existing code:**
> "Review this OpenTofu configuration following GCP best practices"

**Generate CI/CD workflow:**
> "Create a Cloud Build pipeline for OpenTofu with security scanning"

**Testing strategy:**
> "Help me choose between native tests and Terratest for my GCP modules"

**Run QA checks:**
> "Run QA checks on my OpenTofu code using the qa_runner script"

## What It Covers

### GCP Services

- **Compute**: Instances, instance groups, templates
- **Networking**: VPC, subnets, firewall rules, Cloud NAT
- **Storage**: GCS buckets, Cloud SQL
- **Containers**: GKE clusters and node pools
- **Artifact Registry**: Docker, npm, Python, Maven repositories
- **Messaging**: Pub/Sub topics and subscriptions
- **IAM**: Service accounts, custom roles, Workload Identity

### OpenTofu Features

| Feature | Version | Description |
|---------|---------|-------------|
| State Encryption | 1.7+ | Client-side encryption with GCP KMS |
| Early Variable Evaluation | 1.8+ | Variables in backend configuration |
| `enabled` Meta-argument | 1.11+ | Conditional resource creation |
| Ephemeral Resources | 1.11+ | Secrets that don't persist in state |

### Testing Strategy Framework

Decision matrices for:
- When to use native tests (OpenTofu 1.7+)
- When to use Terratest (Go-based)
- GCP-specific testing patterns

### Module Development Patterns

- Naming conventions (`tofu-google-<NAME>`)
- Directory structure best practices
- Required GCP labels template
- Input variable organization
- Output value design

### CI/CD Workflows

- Cloud Build templates with security scanning
- GitHub Actions with Workload Identity Federation
- GitLab CI templates
- Security scanning integration (Trivy, Checkov)

### Security & Compliance

- Three-tier security scanning approach
- State encryption with GCP KMS
- Google Secret Manager integration
- VPC Service Controls
- Common GCP security misconfigurations to avoid

### QA Automation

The included `scripts/qa_runner.py` runs:
- `tofu fmt` - Code formatting
- `tofu validate` - Configuration validation
- `tflint` - Linting and best practices
- `trivy` - IaC misconfiguration scanning
- `checkov` - Policy compliance scanning

```bash
python scripts/qa_runner.py /path/to/tofu/project
```

## Why This Skill?

**OpenTofu-Native:**
- Leverages OpenTofu-unique features (state encryption, enabled meta-argument)
- Uses only `tofu` commands (no Terraform references)
- Up-to-date with OpenTofu 1.7+ features

**GCP-Optimized:**
- GCP-specific patterns and best practices
- Google Cloud service examples throughout
- Workload Identity Federation for CI/CD
- GCS backend with state encryption

**Production-Tested:**
- Patterns from real-world GCP deployments
- Security scanning integration
- Compliance automation workflows

**Decision Frameworks:**
Not just "what to do" but "when and why" - helping you make informed architecture decisions.

## Requirements

- **Claude Code** or other Claude environment supporting skills
- **OpenTofu** 1.7+ (1.11+ recommended for latest features)
- **GCP Project** with appropriate permissions
- Optional: MCP tools for enhanced registry integration

### QA Runner Requirements

For the QA runner script:
- Python 3.8+
- `tofu` (OpenTofu CLI)
- `tflint`
- `trivy`
- `checkov`

## Contributing

See [CLAUDE.md](CLAUDE.md) for:
- Skill development guidelines
- Content structure philosophy
- How to propose improvements
- Testing and validation approach

**Issues & Feedback:**
[GitHub Issues](https://github.com/antonbabenko/opentofu-skill-gcp/issues)

## Releases

Releases are automated based on conventional commits in commit messages:

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat!:` or `BREAKING CHANGE:` | Major | 1.2.3 → 2.0.0 |
| `feat:` | Minor | 1.2.3 → 1.3.0 |
| `fix:` | Patch | 1.2.3 → 1.2.4 |
| Other commits | Patch (default) | 1.2.3 → 1.2.4 |

Releases are created automatically when changes are pushed to master.

## License & Attribution

**License:** Apache 2.0 - see [LICENSE](LICENSE)

**Sources:**
- [OpenTofu Documentation](https://opentofu.org/docs/)
- [Google Cloud Best Practices](https://cloud.google.com/docs/terraform/best-practices-for-terraform)
- [terraform-best-practices.com](https://terraform-best-practices.com)
- Community expertise

## Related Resources

- [OpenTofu Documentation](https://opentofu.org/docs/) - Official OpenTofu docs
- [Google Cloud Terraform Docs](https://cloud.google.com/docs/terraform) - GCP provider reference
- [terraform-google-modules](https://github.com/terraform-google-modules) - Community GCP modules
- [Trivy](https://aquasecurity.github.io/trivy/) - Security scanner
- [Checkov](https://www.checkov.io/) - Policy-as-code
- [Prowler](https://prowler.pro/) - Cloud security posture
