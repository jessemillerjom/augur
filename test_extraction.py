#!/usr/bin/env python3
"""
Test script to verify the regression test extraction logic.
"""

import re

def test_regression_test_extraction():
    """Test the regression test extraction logic."""
    
    # Sample report text that includes a regression test section
    sample_report = """
# Post-Mortem: Checkout Service Disruption on 2024-01-15

## Summary
On 2024-01-15 between 14:05 and 14:45 UTC, the checkout-service and products-api experienced elevated error rates and increased response times.

## Timeline of Events
- **2024-01-15 14:05:00:** auth-service reports high memory usage (90%)
- **2024-01-15 14:10:00:** auth-service critical memory pressure and restart

## Root Cause Analysis
The root cause of the incident was excessive memory consumption by the auth-service.

## Action Items
- Investigate auth-service memory usage
- Implement memory monitoring and alerting

## Timeline Events (for chart)
```json
[
  {"time": "2024-01-15 14:05:00", "event": "auth-service high memory usage (90%)"},
  {"time": "2024-01-15 14:10:00", "event": "auth-service critical memory pressure and restart"}
]
```

## Suggested Monitoring as Code
```terraform
resource "datadog_monitor" "auth_service_memory_usage" {
  name = "Auth Service High Memory Usage"
  type = "metric alert"
  message = "Auth service memory usage is critically high."
  query = "avg(last_5m):avg:auth_service.memory.usage{environment:prod} > 90"
}
```

## Suggested Regression Test
```python
import pytest

def test_auth_service_memory_usage(auth_service_fixture):
    """
    This test verifies that the auth service's memory usage remains within acceptable limits
    under high load.
    """
    # Simulate high load on the auth service
    for _ in range(10000):
        auth_service_fixture.create_user(f"test_user_{_}")

    # Check memory usage after simulating the load
    memory_usage = auth_service_fixture.get_memory_usage()
    assert memory_usage < 90, f"Memory usage exceeded acceptable limit: {memory_usage}%"
```
"""

    print("Original report length:", len(sample_report))
    print("\n" + "="*50)
    print("ORIGINAL REPORT:")
    print("="*50)
    print(sample_report)
    
    # Test the extraction logic
    regression_test_code = ""
    monitoring_code = ""
    
    # More robust regex to match the monitoring code section with various header formats
    monitoring_patterns = [
        r"#+\s*Suggested Monitoring as Code\s*\n(.*?)(?=\n#+|\Z)",
        r"##\s*Suggested Monitoring as Code\s*\n(.*?)(?=\n#+|\Z)",
        r"###\s*Suggested Monitoring as Code\s*\n(.*?)(?=\n#+|\Z)",
        r"#+\s*Suggested Monitoring as Code\s*(.*?)(?=\n#+|\Z)"
    ]
    
    for pattern in monitoring_patterns:
        monitoring_match = re.search(pattern, sample_report, re.DOTALL | re.IGNORECASE)
        if monitoring_match:
            monitoring_code = monitoring_match.group(1).strip()
            # Remove the entire section (heading and content) from the main report
            sample_report = re.sub(pattern, "", sample_report, flags=re.DOTALL | re.IGNORECASE).strip()
            break
    
    # More robust regex to match the regression test section with various header formats
    regression_patterns = [
        r"#+\s*Suggested Regression Test\s*\n(.*?)(?=\n#+|\Z)",
        r"##\s*Suggested Regression Test\s*\n(.*?)(?=\n#+|\Z)",
        r"###\s*Suggested Regression Test\s*\n(.*?)(?=\n#+|\Z)",
        r"#+\s*Suggested Regression Test\s*(.*?)(?=\n#+|\Z)"
    ]
    
    for pattern in regression_patterns:
        regression_match = re.search(pattern, sample_report, re.DOTALL | re.IGNORECASE)
        if regression_match:
            regression_test_code = regression_match.group(1).strip()
            # Remove the entire section (heading and content) from the main report
            sample_report = re.sub(pattern, "", sample_report, flags=re.DOTALL | re.IGNORECASE).strip()
            break
    
    print("\n" + "="*50)
    print("EXTRACTED MONITORING CODE:")
    print("="*50)
    print(monitoring_code)
    
    print("\n" + "="*50)
    print("EXTRACTED REGRESSION TEST CODE:")
    print("="*50)
    print(regression_test_code)
    
    print("\n" + "="*50)
    print("CLEANED REPORT (without extracted sections):")
    print("="*50)
    print(sample_report)
    
    print("\n" + "="*50)
    print("TEST RESULTS:")
    print("="*50)
    print(f"Monitoring code extracted: {'✓' if monitoring_code else '✗'}")
    print(f"Regression test extracted: {'✓' if regression_test_code else '✗'}")
    print(f"Regression test removed from main report: {'✓' if 'Suggested Regression Test' not in sample_report else '✗'}")
    print(f"Monitoring code removed from main report: {'✓' if 'Suggested Monitoring as Code' not in sample_report else '✗'}")

if __name__ == "__main__":
    test_regression_test_extraction() 