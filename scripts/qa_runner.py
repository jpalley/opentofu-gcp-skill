#!/usr/bin/env python3
"""OpenTofu QA Runner for GCP Infrastructure

Runs comprehensive quality and security checks for OpenTofu/GCP projects:
- tofu fmt: Code formatting
- tofu validate: Configuration validation
- tflint: Linting and best practices
- trivy: IaC misconfiguration scanning (AVD-GCP-* checks)
- checkov: Policy compliance (CKV_GCP_* checks)

Usage:
    python qa_runner.py [target_directory]
    python qa_runner.py .
    python qa_runner.py /path/to/tofu/project

Requirements:
    - tofu (OpenTofu CLI)
    - tflint
    - trivy
    - checkov

For post-deploy cloud posture assessment, use prowler separately:
    prowler gcp --project-id my-project
"""

import subprocess
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CheckResult:
    """Result of a single QA check."""
    name: str
    passed: bool
    output: str
    errors: str
    return_code: int
    duration_seconds: float


class QARunner:
    """OpenTofu QA Runner for GCP Infrastructure.

    Runs comprehensive quality and security checks including:
    - Format checking (tofu fmt)
    - Validation (tofu validate)
    - Linting (tflint)
    - Security scanning (trivy, checkov)
    """

    # Check definitions: (name, command, output_type, description)
    CHECKS: List[Tuple[str, List[str], str, str]] = [
        (
            "Format",
            ["tofu", "fmt", "-check", "-recursive"],
            "text",
            "Check OpenTofu code formatting"
        ),
        (
            "Validate",
            ["tofu", "validate"],
            "text",
            "Validate OpenTofu configuration"
        ),
        (
            "TFLint",
            ["tflint", "--format=json"],
            "json",
            "Lint configuration for best practices"
        ),
        (
            "Trivy",
            ["trivy", "config", ".", "--severity", "CRITICAL,HIGH,MEDIUM", "--format", "json"],
            "json",
            "Scan for IaC misconfigurations (AVD-GCP-* checks)"
        ),
        (
            "Checkov",
            ["checkov", "-d", ".", "--framework", "terraform", "-o", "json", "--compact"],
            "json",
            "Policy compliance scanning (CKV_GCP_* checks)"
        ),
    ]

    # Required tools and their version commands
    REQUIRED_TOOLS: Dict[str, List[str]] = {
        "tofu": ["tofu", "--version"],
        "tflint": ["tflint", "--version"],
        "trivy": ["trivy", "--version"],
        "checkov": ["checkov", "--version"],
    }

    def __init__(self, target: str = "."):
        """Initialize QA Runner.

        Args:
            target: Directory to run checks against (default: current directory)
        """
        self.target = Path(target).resolve()
        self.results: Dict[str, CheckResult] = {}
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def check_prerequisites(self) -> Dict[str, bool]:
        """Verify required tools are installed.

        Returns:
            Dictionary mapping tool name to availability status
        """
        tool_status = {}
        for tool, version_cmd in self.REQUIRED_TOOLS.items():
            try:
                subprocess.run(
                    version_cmd,
                    capture_output=True,
                    check=True,
                    timeout=10
                )
                tool_status[tool] = True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                tool_status[tool] = False
        return tool_status

    def get_missing_tools(self) -> List[str]:
        """Get list of missing required tools.

        Returns:
            List of tool names that are not available
        """
        status = self.check_prerequisites()
        return [tool for tool, available in status.items() if not available]

    def run_init_if_needed(self) -> bool:
        """Run tofu init if .terraform directory doesn't exist.

        Returns:
            True if init was successful or not needed, False otherwise
        """
        terraform_dir = self.target / ".terraform"
        if not terraform_dir.exists():
            print("Running 'tofu init' (required for validation)...")
            try:
                result = subprocess.run(
                    ["tofu", "init", "-backend=false"],
                    capture_output=True,
                    text=True,
                    cwd=self.target,
                    timeout=300
                )
                if result.returncode != 0:
                    print(f"Warning: tofu init failed: {result.stderr}")
                    return False
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                print(f"Warning: tofu init failed: {e}")
                return False
        return True

    def run_all(self) -> Dict[str, CheckResult]:
        """Run all QA checks.

        Returns:
            Dictionary mapping check name to CheckResult
        """
        self.start_time = datetime.now()

        # Ensure tofu is initialized for validate to work
        self.run_init_if_needed()

        for name, cmd, output_type, description in self.CHECKS:
            print(f"Running {name}... ", end="", flush=True)
            self.results[name] = self._run_check(name, cmd, output_type, description)
            status = "PASS" if self.results[name].passed else "FAIL"
            print(status)

        self.end_time = datetime.now()
        return self.results

    def _run_check(
        self,
        name: str,
        cmd: List[str],
        output_type: str,
        description: str
    ) -> CheckResult:
        """Execute a single check and capture results.

        Args:
            name: Check name
            cmd: Command to execute
            output_type: Expected output type ("text" or "json")
            description: Human-readable description

        Returns:
            CheckResult with execution details
        """
        start = datetime.now()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.target,
                timeout=600  # 10 minute timeout
            )
            duration = (datetime.now() - start).total_seconds()

            # Parse JSON output if expected
            output = result.stdout
            if output_type == "json" and result.stdout.strip():
                try:
                    parsed = json.loads(result.stdout)
                    output = json.dumps(parsed, indent=2)
                except json.JSONDecodeError:
                    pass  # Keep raw output if JSON parsing fails

            return CheckResult(
                name=name,
                passed=result.returncode == 0,
                output=output,
                errors=result.stderr,
                return_code=result.returncode,
                duration_seconds=duration
            )
        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start).total_seconds()
            return CheckResult(
                name=name,
                passed=False,
                output="",
                errors=f"Check timed out after {duration:.1f} seconds",
                return_code=-1,
                duration_seconds=duration
            )
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            return CheckResult(
                name=name,
                passed=False,
                output="",
                errors=str(e),
                return_code=-1,
                duration_seconds=duration
            )

    def run_prowler(self, project_id: str, output_dir: Optional[str] = None) -> CheckResult:
        """Run Prowler against deployed GCP infrastructure.

        This is a post-deploy check that audits actual cloud resources.

        Args:
            project_id: GCP project ID to scan
            output_dir: Optional directory for output files

        Returns:
            CheckResult with Prowler findings
        """
        cmd = [
            "prowler", "gcp",
            "--project-id", project_id,
            "--compliance", "cis_gcp",
            "--output-formats", "json"
        ]

        if output_dir:
            cmd.extend(["--output-directory", output_dir])

        print(f"Running Prowler against project {project_id}... ", flush=True)
        result = self._run_check("Prowler", cmd, "json", "Cloud posture assessment")
        print("PASS" if result.passed else "FAIL")

        return result

    def generate_report(self) -> str:
        """Generate markdown QA report.

        Returns:
            Markdown-formatted report string
        """
        lines = [
            "# OpenTofu GCP QA Report",
            "",
            f"**Target:** `{self.target}`",
            f"**Generated:** {datetime.now().isoformat()}",
            ""
        ]

        # Summary
        passed = sum(1 for r in self.results.values() if r.passed)
        total = len(self.results)
        status_emoji = "✅" if passed == total else "❌"

        lines.append(f"## Summary: {status_emoji} {passed}/{total} checks passed")
        lines.append("")

        # Duration
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            lines.append(f"**Total Duration:** {duration:.1f} seconds")
            lines.append("")

        # Quick status table
        lines.append("| Check | Status | Duration |")
        lines.append("|-------|--------|----------|")
        for name, result in self.results.items():
            status = "✅ Pass" if result.passed else "❌ Fail"
            lines.append(f"| {name} | {status} | {result.duration_seconds:.1f}s |")
        lines.append("")

        # Detailed results
        lines.append("## Detailed Results")
        lines.append("")

        for name, result in self.results.items():
            status = "✅" if result.passed else "❌"
            lines.append(f"### {status} {name}")
            lines.append("")

            if not result.passed:
                if result.errors:
                    lines.append("**Errors:**")
                    lines.append("```")
                    lines.append(result.errors.strip())
                    lines.append("```")
                    lines.append("")

                if result.output and len(result.output.strip()) < 5000:
                    lines.append("**Output:**")
                    lines.append("```")
                    lines.append(result.output.strip())
                    lines.append("```")
                    lines.append("")
                elif result.output:
                    lines.append("**Output:** (truncated, see full output in logs)")
                    lines.append("```")
                    lines.append(result.output[:2000].strip())
                    lines.append("...")
                    lines.append("```")
                    lines.append("")
            else:
                lines.append("No issues found.")
                lines.append("")

        # Recommendations
        if passed < total:
            lines.append("## Recommendations")
            lines.append("")
            for name, result in self.results.items():
                if not result.passed:
                    if name == "Format":
                        lines.append(f"- **{name}:** Run `tofu fmt -recursive` to fix formatting")
                    elif name == "Validate":
                        lines.append(f"- **{name}:** Fix configuration errors before proceeding")
                    elif name == "TFLint":
                        lines.append(f"- **{name}:** Review and fix linting issues")
                    elif name == "Trivy":
                        lines.append(f"- **{name}:** Address security misconfigurations (AVD-GCP-* checks)")
                    elif name == "Checkov":
                        lines.append(f"- **{name}:** Fix policy violations (CKV_GCP_* checks)")
            lines.append("")

        return "\n".join(lines)

    def generate_json_report(self) -> str:
        """Generate JSON report for CI/CD integration.

        Returns:
            JSON-formatted report string
        """
        report = {
            "target": str(self.target),
            "generated": datetime.now().isoformat(),
            "summary": {
                "passed": sum(1 for r in self.results.values() if r.passed),
                "total": len(self.results),
                "all_passed": all(r.passed for r in self.results.values())
            },
            "checks": {
                name: {
                    "passed": r.passed,
                    "return_code": r.return_code,
                    "duration_seconds": r.duration_seconds,
                    "errors": r.errors if not r.passed else None
                }
                for name, r in self.results.items()
            }
        }
        return json.dumps(report, indent=2)


def main():
    """Main entry point for QA runner."""
    # Parse arguments
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    output_format = "markdown"  # Default to markdown

    # Check for format flag
    if "--json" in sys.argv:
        output_format = "json"
        sys.argv.remove("--json")

    # Initialize runner
    runner = QARunner(target)

    # Check prerequisites
    missing = runner.get_missing_tools()
    if missing:
        print(f"Error: Missing required tools: {', '.join(missing)}")
        print("\nInstallation instructions:")
        print("  tofu:    https://opentofu.org/docs/intro/install/")
        print("  tflint:  https://github.com/terraform-linters/tflint")
        print("  trivy:   https://aquasecurity.github.io/trivy/")
        print("  checkov: pip install checkov")
        sys.exit(1)

    # Run checks
    print(f"\nOpenTofu GCP QA Runner")
    print(f"Target: {runner.target}")
    print("-" * 40)

    runner.run_all()

    print("-" * 40)

    # Generate report
    if output_format == "json":
        print(runner.generate_json_report())
    else:
        print(runner.generate_report())

    # Exit with appropriate code
    all_passed = all(r.passed for r in runner.results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
