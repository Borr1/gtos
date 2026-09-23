"""Automated Test Runner and Validation Framework.

This module provides automated test runners, validation frameworks, and
comprehensive test coverage reporting for the security and infrastructure
improvements.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

import pytest


@dataclass
class TestResult:
    """Test execution result."""
    name: str
    status: str  # "PASS", "FAIL", "SKIP", "ERROR"
    duration: float
    error_message: Optional[str] = None
    test_file: Optional[str] = None


@dataclass
class TestSuiteResult:
    """Test suite execution result."""
    suite_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    coverage_percent: float
    tests: List[TestResult]
    timestamp: str


@dataclass
class ValidationReport:
    """Complete validation report."""
    timestamp: str
    total_suites: int
    overall_passed: int
    overall_failed: int
    overall_coverage: float
    suite_results: List[TestSuiteResult]
    recommendations: List[str]


class TestAutomationFramework:
    """Automated testing and validation framework."""

    def __init__(self, project_root: Path):
        """Initialize the automation framework.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.test_dir = project_root / "tests"
        self.results_dir = project_root / "test_results"
        self.results_dir.mkdir(exist_ok=True)

    def run_security_tests(self) -> TestSuiteResult:
        """Run security framework tests."""
        return self._run_test_suite(
            "Security Framework",
            "test_security_framework.py"
        )

    def run_infrastructure_tests(self) -> TestSuiteResult:
        """Run infrastructure framework tests."""
        return self._run_test_suite(
            "Infrastructure Framework",
            "test_infrastructure_framework.py"
        )

    def run_integration_tests(self) -> TestSuiteResult:
        """Run end-to-end integration tests."""
        return self._run_test_suite(
            "Integration Framework",
            "test_end_to_end_integration.py"
        )

    def run_all_tests(self) -> ValidationReport:
        """Run all test suites and generate comprehensive report."""
        start_time = time.time()

        # Run all test suites
        suite_results = []

        print("Running Security Framework Tests...")
        security_results = self.run_security_tests()
        suite_results.append(security_results)

        print("Running Infrastructure Framework Tests...")
        infra_results = self.run_infrastructure_tests()
        suite_results.append(infra_results)

        print("Running Integration Framework Tests...")
        integration_results = self.run_integration_tests()
        suite_results.append(integration_results)

        # Calculate overall statistics
        total_passed = sum(r.passed for r in suite_results)
        total_failed = sum(r.failed for r in suite_results)
        total_tests = sum(r.total_tests for r in suite_results)

        overall_coverage = sum(r.coverage_percent for r in suite_results) / len(suite_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(suite_results)

        # Create validation report
        report = ValidationReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_suites=len(suite_results),
            overall_passed=total_passed,
            overall_failed=total_failed,
            overall_coverage=overall_coverage,
            suite_results=suite_results,
            recommendations=recommendations
        )

        # Save report
        self._save_validation_report(report)

        return report

    def _run_test_suite(self, suite_name: str, test_file: str) -> TestSuiteResult:
        """Run a specific test suite.

        Args:
            suite_name: Name of the test suite
            test_file: Test file to run

        Returns:
            Test suite result
        """
        start_time = time.time()
        test_path = self.test_dir / test_file

        if not test_path.exists():
            return TestSuiteResult(
                suite_name=suite_name,
                total_tests=0,
                passed=0,
                failed=1,
                skipped=0,
                errors=0,
                duration=0.0,
                coverage_percent=0.0,
                tests=[TestResult(
                    name=test_file,
                    status="ERROR",
                    duration=0.0,
                    error_message=f"Test file not found: {test_path}",
                    test_file=test_file
                )],
                timestamp=datetime.now(timezone.utc).isoformat()
            )

        # Run pytest with coverage and JSON output
        # Create file names
        suite_slug = suite_name.lower().replace(' ', '_')
        json_report_file = self.results_dir / f"{suite_slug}.json"
        coverage_report_file = self.results_dir / f"{suite_slug}_coverage.json"

        cmd = [
            sys.executable, "-m", "pytest",
            str(test_path),
            "--json-report",
            f"--json-report-file={json_report_file}",
            "--cov=src",
            "--cov-report=json",
            f"--cov-report=json:{coverage_report_file}",
            "-v"
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Use the same file names as created above

            tests = []
            total_tests = 0
            passed = 0
            failed = 0
            skipped = 0
            errors = 0

            # Parse test results
            if json_report_file.exists():
                with open(json_report_file) as f:
                    data = json.load(f)

                total_tests = data.get("summary", {}).get("total", 0)
                passed = data.get("summary", {}).get("passed", 0)
                failed = data.get("summary", {}).get("failed", 0)
                skipped = data.get("summary", {}).get("skipped", 0)
                errors = data.get("summary", {}).get("error", 0)

                for test in data.get("tests", []):
                    tests.append(TestResult(
                        name=test["nodeid"],
                        status=test["outcome"].upper(),
                        duration=test.get("duration", 0.0),
                        error_message=test.get("call", {}).get("longrepr", None) if test["outcome"] != "passed" else None,
                        test_file=test_file
                    ))

            # Parse coverage
            coverage_percent = 0.0
            if coverage_report_file.exists():
                with open(coverage_report_file) as f:
                    coverage_data = json.load(f)
                    coverage_percent = coverage_data.get("totals", {}).get("percent_covered", 0.0)

            duration = time.time() - start_time

            return TestSuiteResult(
                suite_name=suite_name,
                total_tests=total_tests,
                passed=passed,
                failed=failed,
                skipped=skipped,
                errors=errors,
                duration=duration,
                coverage_percent=coverage_percent,
                tests=tests,
                timestamp=datetime.now(timezone.utc).isoformat()
            )

        except subprocess.TimeoutExpired:
            return TestSuiteResult(
                suite_name=suite_name,
                total_tests=0,
                passed=0,
                failed=1,
                skipped=0,
                errors=0,
                duration=300.0,
                coverage_percent=0.0,
                tests=[TestResult(
                    name="timeout",
                    status="ERROR",
                    duration=300.0,
                    error_message="Test suite timed out after 5 minutes",
                    test_file=test_file
                )],
                timestamp=datetime.now(timezone.utc).isoformat()
            )

        except Exception as e:
            duration = time.time() - start_time
            return TestSuiteResult(
                suite_name=suite_name,
                total_tests=0,
                passed=0,
                failed=1,
                skipped=0,
                errors=0,
                duration=duration,
                coverage_percent=0.0,
                tests=[TestResult(
                    name="error",
                    status="ERROR",
                    duration=duration,
                    error_message=str(e),
                    test_file=test_file
                )],
                timestamp=datetime.now(timezone.utc).isoformat()
            )

    def _generate_recommendations(self, suite_results: List[TestSuiteResult]) -> List[str]:
        """Generate recommendations based on test results.

        Args:
            suite_results: List of test suite results

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Overall coverage recommendation
        avg_coverage = sum(r.coverage_percent for r in suite_results) / len(suite_results)
        if avg_coverage < 80:
            recommendations.append(
                f"Increase test coverage from {avg_coverage:.1f}% to at least 80%"
            )

        # Failed tests recommendations
        for suite in suite_results:
            if suite.failed > 0:
                recommendations.append(
                    f"Fix {suite.failed} failing tests in {suite.suite_name}"
                )

            # Performance recommendations
            if suite.duration > 60:  # More than 1 minute
                recommendations.append(
                    f"Optimize {suite.suite_name} test performance (current: {suite.duration:.1f}s)"
                )

        # Specific test failure analysis
        for suite in suite_results:
            for test in suite.tests:
                if test.status == "FAIL" and test.error_message:
                    if "timeout" in test.error_message.lower():
                        recommendations.append(
                            f"Investigate timeout in {test.name} - may indicate performance issues"
                        )
                    elif "assertion" in test.error_message.lower():
                        recommendations.append(
                            f"Review assertion logic in {test.name}"
                        )

        # Infrastructure-specific recommendations
        infra_suite = next((s for s in suite_results if "Infrastructure" in s.suite_name), None)
        if infra_suite and infra_suite.failed > 0:
            recommendations.append(
                "Infrastructure test failures may indicate monitoring system issues"
            )

        # Security-specific recommendations
        security_suite = next((s for s in suite_results if "Security" in s.suite_name), None)
        if security_suite and security_suite.failed > 0:
            recommendations.append(
                "Security test failures require immediate attention - potential security vulnerabilities"
            )

        return recommendations

    def _save_validation_report(self, report: ValidationReport) -> None:
        """Save validation report to file.

        Args:
            report: Validation report to save
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"validation_report_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(asdict(report), f, indent=2)

        # Also save as latest
        latest_file = self.results_dir / "latest_validation_report.json"
        with open(latest_file, "w") as f:
            json.dump(asdict(report), f, indent=2)

    def generate_html_report(self, report: ValidationReport) -> Path:
        """Generate HTML report from validation results.

        Args:
            report: Validation report

        Returns:
            Path to generated HTML report
        """
        html_content = self._create_html_report(report)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        html_file = self.results_dir / f"test_report_{timestamp}.html"

        with open(html_file, "w") as f:
            f.write(html_content)

        # Also save as latest
        latest_file = self.results_dir / "latest_test_report.html"
        with open(latest_file, "w") as f:
            f.write(html_content)

        return html_file

    def _create_html_report(self, report: ValidationReport) -> str:
        """Create HTML report content.

        Args:
            report: Validation report

        Returns:
            HTML content string
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .suite {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }}
        .suite-header {{ background-color: #e9e9e9; padding: 10px; font-weight: bold; }}
        .suite-content {{ padding: 10px; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .skip {{ color: orange; }}
        .error {{ color: purple; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f0f0f0; }}
        .recommendations {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Test Validation Report</h1>
        <p><strong>Generated:</strong> {report.timestamp}</p>
        <p><strong>Overall Status:</strong>
            <span class="{'pass' if report.overall_failed == 0 else 'fail'}">
                {report.overall_passed} passed, {report.overall_failed} failed
            </span>
        </p>
        <p><strong>Coverage:</strong> {report.overall_coverage:.1f}%</p>
    </div>

    <div class="summary">
        <h2>Test Suite Summary</h2>
        <table>
            <tr>
                <th>Suite</th>
                <th>Total</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Skipped</th>
                <th>Coverage</th>
                <th>Duration</th>
            </tr>
        """

        for suite in report.suite_results:
            html += f"""
            <tr>
                <td>{suite.suite_name}</td>
                <td>{suite.total_tests}</td>
                <td class="pass">{suite.passed}</td>
                <td class="{'fail' if suite.failed > 0 else ''}">{suite.failed}</td>
                <td class="skip">{suite.skipped}</td>
                <td>{suite.coverage_percent:.1f}%</td>
                <td>{suite.duration:.1f}s</td>
            </tr>
            """

        html += """
        </table>
    </div>
    """

        # Detailed results for each suite
        for suite in report.suite_results:
            html += f"""
    <div class="suite">
        <div class="suite-header">{suite.suite_name}</div>
        <div class="suite-content">
            <p><strong>Status:</strong> {suite.passed}/{suite.total_tests} tests passed</p>
            <p><strong>Coverage:</strong> {suite.coverage_percent:.1f}%</p>
            <p><strong>Duration:</strong> {suite.duration:.1f} seconds</p>
            """

            if suite.tests:
                html += """
            <h4>Test Details</h4>
            <table>
                <tr><th>Test</th><th>Status</th><th>Duration</th><th>Error</th></tr>
                """

                for test in suite.tests:
                    status_class = test.status.lower()
                    error_msg = test.error_message or ""
                    if len(error_msg) > 100:
                        error_msg = error_msg[:100] + "..."

                    html += f"""
                <tr>
                    <td>{test.name}</td>
                    <td class="{status_class}">{test.status}</td>
                    <td>{test.duration:.2f}s</td>
                    <td>{error_msg}</td>
                </tr>
                    """

                html += "</table>"

            html += "</div></div>"

        # Recommendations
        if report.recommendations:
            html += """
    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>
            """
            for rec in report.recommendations:
                html += f"<li>{rec}</li>"

            html += """
        </ul>
    </div>
            """

        html += """
</body>
</html>
        """

        return html


class ContinuousValidation:
    """Continuous validation and monitoring for test health."""

    def __init__(self, project_root: Path, interval_minutes: int = 60):
        """Initialize continuous validation.

        Args:
            project_root: Root directory of the project
            interval_minutes: Validation interval in minutes
        """
        self.framework = TestAutomationFramework(project_root)
        self.interval_minutes = interval_minutes
        self.running = False
        self.thread = None

    def start(self) -> None:
        """Start continuous validation."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._validation_loop, daemon=True)
        self.thread.start()
        print(f"Started continuous validation (every {self.interval_minutes} minutes)")

    def stop(self) -> None:
        """Stop continuous validation."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _validation_loop(self) -> None:
        """Continuous validation loop."""
        while self.running:
            try:
                print("Running automated validation...")
                report = self.framework.run_all_tests()

                # Generate HTML report
                html_file = self.framework.generate_html_report(report)
                print(f"Validation complete. Report: {html_file}")

                # Alert on failures
                if report.overall_failed > 0:
                    print(f"ALERT: {report.overall_failed} tests failed!")
                    self._send_failure_alert(report)

                # Wait for next interval
                time.sleep(self.interval_minutes * 60)

            except Exception as e:
                print(f"Error in validation loop: {e}")
                time.sleep(60)  # Wait 1 minute on error

    def _send_failure_alert(self, report: ValidationReport) -> None:
        """Send alert for test failures.

        Args:
            report: Validation report with failures
        """
        # In a real system, this would send alerts via email, Slack, etc.
        print(f"FAILURE ALERT: {report.overall_failed} tests failed")
        for suite in report.suite_results:
            if suite.failed > 0:
                print(f"  - {suite.suite_name}: {suite.failed} failures")


# ═══════════════════════════════════════════════════════════════════════
# Test Framework Validation Tests
# ═══════════════════════════════════════════════════════════════════════

class TestTestAutomationFramework:
    """Tests for the test automation framework itself."""

    def test_framework_initialization(self, tmp_path):
        """Test framework initialization."""
        framework = TestAutomationFramework(tmp_path)

        assert framework.project_root == tmp_path
        assert framework.test_dir == tmp_path / "tests"
        assert framework.results_dir.exists()

    def test_test_result_creation(self):
        """Test TestResult dataclass creation."""
        result = TestResult(
            name="test_example",
            status="PASS",
            duration=1.5,
            test_file="test_file.py"
        )

        assert result.name == "test_example"
        assert result.status == "PASS"
        assert result.duration == 1.5
        assert result.error_message is None

    def test_validation_report_generation(self):
        """Test validation report generation."""
        suite_result = TestSuiteResult(
            suite_name="Test Suite",
            total_tests=10,
            passed=8,
            failed=2,
            skipped=0,
            errors=0,
            duration=30.0,
            coverage_percent=85.0,
            tests=[],
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        report = ValidationReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_suites=1,
            overall_passed=8,
            overall_failed=2,
            overall_coverage=85.0,
            suite_results=[suite_result],
            recommendations=["Fix 2 failing tests"]
        )

        assert report.total_suites == 1
        assert report.overall_passed == 8
        assert report.overall_failed == 2
        assert len(report.recommendations) == 1

    def test_recommendation_generation(self, tmp_path):
        """Test recommendation generation logic."""
        framework = TestAutomationFramework(tmp_path)

        # Create suite with low coverage
        low_coverage_suite = TestSuiteResult(
            suite_name="Low Coverage Suite",
            total_tests=10,
            passed=10,
            failed=0,
            skipped=0,
            errors=0,
            duration=30.0,
            coverage_percent=60.0,  # Below 80%
            tests=[],
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Create suite with failures
        failing_suite = TestSuiteResult(
            suite_name="Failing Suite",
            total_tests=5,
            passed=3,
            failed=2,
            skipped=0,
            errors=0,
            duration=45.0,
            coverage_percent=85.0,
            tests=[],
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        recommendations = framework._generate_recommendations([low_coverage_suite, failing_suite])

        assert len(recommendations) >= 2
        assert any("coverage" in rec.lower() for rec in recommendations)
        assert any("failing tests" in rec.lower() for rec in recommendations)

    def test_html_report_generation(self, tmp_path):
        """Test HTML report generation."""
        framework = TestAutomationFramework(tmp_path)

        suite_result = TestSuiteResult(
            suite_name="Test Suite",
            total_tests=5,
            passed=4,
            failed=1,
            skipped=0,
            errors=0,
            duration=15.0,
            coverage_percent=90.0,
            tests=[
                TestResult("test_pass", "PASS", 1.0, test_file="test.py"),
                TestResult("test_fail", "FAIL", 2.0, "Assertion failed", "test.py")
            ],
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        report = ValidationReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_suites=1,
            overall_passed=4,
            overall_failed=1,
            overall_coverage=90.0,
            suite_results=[suite_result],
            recommendations=["Fix failing test"]
        )

        html_content = framework._create_html_report(report)

        assert "Test Validation Report" in html_content
        assert "Test Suite" in html_content
        assert "90.0%" in html_content
        assert "test_pass" in html_content
        assert "test_fail" in html_content

    def test_continuous_validation_lifecycle(self, tmp_path):
        """Test continuous validation start/stop."""
        validator = ContinuousValidation(tmp_path, interval_minutes=1)

        assert not validator.running

        validator.start()
        assert validator.running
        assert validator.thread is not None

        validator.stop()
        assert not validator.running


if __name__ == "__main__":
    # Example usage
    project_root = Path("/Users/borr/Documents/trading/gold-agent/.climpire-worktrees/5f598956")
    framework = TestAutomationFramework(project_root)

    # Run all tests and generate report
    report = framework.run_all_tests()
    html_file = framework.generate_html_report(report)

    print(f"Validation complete!")
    print(f"Tests: {report.overall_passed} passed, {report.overall_failed} failed")
    print(f"Coverage: {report.overall_coverage:.1f}%")
    print(f"Report: {html_file}")

    if report.recommendations:
        print("\nRecommendations:")
        for rec in report.recommendations:
            print(f"  - {rec}")