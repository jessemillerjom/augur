import json
import csv
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# --- Find project root (directory containing 'incidents') ---
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
INCIDENTS_ROOT = PROJECT_ROOT / "incidents"

# Shared services across all scenarios
SERVICES = {
    "auth-service": "auth-db",
    "products-api": "products-db", 
    "checkout-service": "checkout-db",
    "payment-gateway": "payment-db",
    "caching-service": "redis",
    "shipping-api": "shipping-db"
}


def create_incident_structure(incident_dir: str) -> tuple[Path, Path, Path]:
    """Create the directory structure for an incident at the project root."""
    incident_path = INCIDENTS_ROOT / incident_dir
    logs_path = incident_path / "logs"
    metrics_path = incident_path / "metrics"
    logs_path.mkdir(parents=True, exist_ok=True)
    metrics_path.mkdir(parents=True, exist_ok=True)
    return incident_path, logs_path, metrics_path


def save_logs(logs_path: Path, service: str, logs: List[Dict[str, Any]]):
    """Save logs to a JSON lines file."""
    log_file = logs_path / f"{service}.log"
    with open(log_file, 'w') as f:
        for log in logs:
            f.write(json.dumps(log) + '\n')


def save_metrics(metrics_path: Path, metrics_data: List[Dict[str, Any]]):
    """Save metrics to a CSV file."""
    metrics_file = metrics_path / "metrics.csv"
    with open(metrics_file, 'w', newline='') as f:
        if metrics_data:
            writer = csv.DictWriter(f, fieldnames=metrics_data[0].keys())
            writer.writeheader()
            writer.writerows(metrics_data)


def generate_bad_deploy_data(incident_dir: str):
    """Incident 1: The Bad Deploy (Simple)"""
    incident_path, logs_path, metrics_path = create_incident_structure(incident_dir)
    
    # Incident timeline
    incident_start = datetime(2024, 1, 15, 14, 5, 0)  # 14:05 - Bad deploy
    incident_end = datetime(2024, 1, 15, 14, 45, 0)   # 14:45 - Rollback
    
    # Generate logs for each service
    services = ["auth-service", "products-api", "checkout-service"]
    
    for service in services:
        logs = []
        current_time = datetime(2024, 1, 15, 13, 0, 0)
        end_time = datetime(2024, 1, 15, 16, 0, 0)
        
        while current_time <= end_time:
            timestamp = current_time.isoformat()
            
            if service == "auth-service":
                if current_time >= incident_start and current_time <= incident_end:
                    # During incident - memory leak symptoms
                    if current_time.minute % 5 == 0:  # Every 5 minutes
                        logs.append({
                            "timestamp": timestamp,
                            "level": "WARN",
                            "service": service,
                            "message": f"Memory usage high: {85 + (current_time.minute % 30)}%",
                            "memory_usage": 85 + (current_time.minute % 30),
                            "cpu_usage": 75 + (current_time.minute % 20)
                        })
                    
                    if current_time.minute % 10 == 0:  # Every 10 minutes
                        logs.append({
                            "timestamp": timestamp,
                            "level": "ERROR",
                            "service": service,
                            "message": "Critical memory pressure, restarting",
                            "memory_usage": 95 + (current_time.minute % 5),
                            "cpu_usage": 90 + (current_time.minute % 10)
                        })
                else:
                    # Normal operation
                    if current_time.minute % 15 == 0:  # Every 15 minutes
                        logs.append({
                            "timestamp": timestamp,
                            "level": "INFO",
                            "service": service,
                            "message": "Service operating normally",
                            "memory_usage": 45 + (current_time.minute % 20),
                            "cpu_usage": 30 + (current_time.minute % 15)
                        })
            
            elif service in ["products-api", "checkout-service"]:
                if current_time >= incident_start and current_time <= incident_end:
                    # During incident - auth service unavailable
                    if current_time.minute % 3 == 0:  # Every 3 minutes
                        logs.append({
                            "timestamp": timestamp,
                            "level": "ERROR",
                            "service": service,
                            "message": "Downstream service auth-service unresponsive",
                            "http_status": 503,
                            "response_time": 5000 + (current_time.minute * 100)
                        })
                    
                    if current_time.minute % 5 == 0:  # Every 5 minutes
                        logs.append({
                            "timestamp": timestamp,
                            "level": "WARN",
                            "service": service,
                            "message": f"High error rate detected: {20 + (current_time.minute % 15)}% of requests failing",
                            "error_rate": 20 + (current_time.minute % 15),
                            "http_status": 500
                        })
                else:
                    # Normal operation
                    if current_time.minute % 10 == 0:  # Every 10 minutes
                        logs.append({
                            "timestamp": timestamp,
                            "level": "INFO",
                            "service": service,
                            "message": "Service operating normally",
                            "http_status": 200,
                            "response_time": 150 + (current_time.minute % 50)
                        })
            
            current_time += timedelta(minutes=1)
        
        save_logs(logs_path, service, logs)
    
    # Generate metrics CSV
    metrics_data = []
    current_time = datetime(2024, 1, 15, 13, 0, 0)
    end_time = datetime(2024, 1, 15, 16, 0, 0)
    
    while current_time <= end_time:
        timestamp = current_time.isoformat()
        
        # Auth service metrics
        if current_time >= incident_start and current_time <= incident_end:
            auth_cpu = 75 + (current_time.minute % 25)
            auth_memory = 85 + (current_time.minute % 15)
        else:
            auth_cpu = 30 + (current_time.minute % 20)
            auth_memory = 45 + (current_time.minute % 25)
        
        # Downstream services metrics
        if current_time >= incident_start and current_time <= incident_end:
            products_errors = 25 + (current_time.minute % 20)
            checkout_errors = 30 + (current_time.minute % 25)
        else:
            products_errors = 1 + (current_time.minute % 3)
            checkout_errors = 1 + (current_time.minute % 2)
        
        metrics_data.append({
            "timestamp": timestamp,
            "auth_service.cpu.utilization": auth_cpu,
            "auth_service.memory.usage": auth_memory,
            "products_api.http.errors.5xx": products_errors,
            "checkout_service.http.errors.5xx": checkout_errors
        })
        
        current_time += timedelta(minutes=1)
    
    save_metrics(metrics_path, metrics_data)
    print(f"Generated 'The Bad Deploy' incident data in: {incident_path}")


def generate_thundering_herd_data(incident_dir: str):
    """Incident 2: The Thundering Herd (Medium)"""
    incident_path, logs_path, metrics_path = create_incident_structure(incident_dir)
    
    # Incident timeline
    incident_start = datetime(2024, 1, 15, 14, 10, 0)  # 14:10 - Traffic spike
    incident_end = datetime(2024, 1, 15, 14, 50, 0)    # 14:50 - Resolution
    
    # Generate logs for products-api
    logs = []
    current_time = datetime(2024, 1, 15, 13, 0, 0)
    end_time = datetime(2024, 1, 15, 16, 0, 0)
    
    while current_time <= end_time:
        timestamp = current_time.isoformat()
        
        if current_time >= incident_start and current_time <= incident_end:
            # During incident - DB connection pool exhausted
            if current_time.minute % 2 == 0:  # Every 2 minutes
                logs.append({
                    "timestamp": timestamp,
                    "level": "ERROR",
                    "service": "products-api",
                    "message": "DB connection pool exhausted. Cannot serve request.",
                    "http_status": 503,
                    "db_connections": 100,
                    "response_time": 30000
                })
            
            if current_time.minute % 5 == 0:  # Every 5 minutes
                logs.append({
                    "timestamp": timestamp,
                    "level": "WARN",
                    "service": "products-api",
                    "message": f"High request volume: {1000 + (current_time.minute * 100)} requests/min",
                    "request_rate": 1000 + (current_time.minute * 100),
                    "cpu_usage": 45 + (current_time.minute % 15)
                })
        else:
            # Normal operation
            if current_time.minute % 10 == 0:  # Every 10 minutes
                logs.append({
                    "timestamp": timestamp,
                    "level": "INFO",
                    "service": "products-api",
                    "message": "Service operating normally",
                    "http_status": 200,
                    "response_time": 150 + (current_time.minute % 50),
                    "request_rate": 50 + (current_time.minute % 20)
                })
        
        current_time += timedelta(minutes=1)
    
    save_logs(logs_path, "products-api", logs)
    
    # Generate metrics CSV
    metrics_data = []
    current_time = datetime(2024, 1, 15, 13, 0, 0)
    end_time = datetime(2024, 1, 15, 16, 0, 0)
    
    while current_time <= end_time:
        timestamp = current_time.isoformat()
        
        if current_time >= incident_start and current_time <= incident_end:
            # Traffic spike metrics
            products_requests = 1000 + (current_time.minute * 100)
            products_errors = 200 + (current_time.minute * 50)
            products_cpu = 45 + (current_time.minute % 15)
            products_db_cpu = 95 + (current_time.minute % 5)
            products_db_connections = 100
        else:
            # Normal metrics
            products_requests = 50 + (current_time.minute % 20)
            products_errors = 1 + (current_time.minute % 3)
            products_cpu = 25 + (current_time.minute % 15)
            products_db_cpu = 30 + (current_time.minute % 20)
            products_db_connections = 20 + (current_time.minute % 15)
        
        metrics_data.append({
            "timestamp": timestamp,
            "products_api.http.requests.total": products_requests,
            "products_api.http.errors.5xx": products_errors,
            "products_api.cpu.utilization": products_cpu,
            "products_db.cpu.utilization": products_db_cpu,
            "products_db.connections.active": products_db_connections
        })
        
        current_time += timedelta(minutes=1)
    
    save_metrics(metrics_path, metrics_data)
    print(f"Generated 'The Thundering Herd' incident data in: {incident_path}")


def generate_silent_cache_killer_data(incident_dir: str):
    """Incident 3: The Silent Killer Cache (Medium-High)"""
    incident_path, logs_path, metrics_path = create_incident_structure(incident_dir)
    
    # Incident timeline
    incident_start = datetime(2024, 1, 15, 14, 0, 0)   # 14:00 - Cache limit hit
    incident_end = datetime(2024, 1, 15, 15, 0, 0)     # 15:00 - Resolution
    
    # Generate logs for all services
    services = ["auth-service", "products-api", "checkout-service", "caching-service"]
    
    for service in services:
        logs = []
        current_time = datetime(2024, 1, 15, 13, 0, 0)
        end_time = datetime(2024, 1, 15, 16, 0, 0)
        
        while current_time <= end_time:
            timestamp = current_time.isoformat()
            
            if service == "caching-service":
                if current_time >= incident_start and current_time <= incident_end:
                    # Cache eviction logs
                    if current_time.minute % 3 == 0:  # Every 3 minutes
                        logs.append({
                            "timestamp": timestamp,
                            "level": "WARN",
                            "service": service,
                            "message": f"Memory limit reached, evicting {100 + (current_time.minute * 50)} keys",
                            "evicted_keys": 100 + (current_time.minute * 50),
                            "memory_usage": 95 + (current_time.minute % 5)
                        })
                else:
                    # Normal operation
                    if current_time.minute % 15 == 0:  # Every 15 minutes
                        logs.append({
                            "timestamp": timestamp,
                            "level": "INFO",
                            "service": service,
                            "message": "Cache operating normally",
                            "memory_usage": 60 + (current_time.minute % 20),
                            "hit_rate": 95 + (current_time.minute % 5)
                        })
            
            elif service in ["auth-service", "products-api", "checkout-service"]:
                if current_time >= incident_start and current_time <= incident_end:
                    # Slow degradation - only start logging warnings after 14:30
                    if current_time >= datetime(2024, 1, 15, 14, 30, 0):
                        if current_time.minute % 5 == 0:  # Every 5 minutes
                            logs.append({
                                "timestamp": timestamp,
                                "level": "WARN",
                                "service": service,
                                "message": "Database query time exceeded threshold",
                                "query_time": 2000 + (current_time.minute * 100),
                                "cache_miss_rate": 80 + (current_time.minute % 20)
                            })
                else:
                    # Normal operation
                    if current_time.minute % 10 == 0:  # Every 10 minutes
                        logs.append({
                            "timestamp": timestamp,
                            "level": "INFO",
                            "service": service,
                            "message": "Service operating normally",
                            "response_time": 150 + (current_time.minute % 50),
                            "cache_hit_rate": 95 + (current_time.minute % 5)
                        })
            
            current_time += timedelta(minutes=1)
        
        save_logs(logs_path, service, logs)
    
    # Generate metrics CSV
    metrics_data = []
    current_time = datetime(2024, 1, 15, 13, 0, 0)
    end_time = datetime(2024, 1, 15, 16, 0, 0)
    
    while current_time <= end_time:
        timestamp = current_time.isoformat()
        
        if current_time >= incident_start and current_time <= incident_end:
            # Cache metrics
            cache_evicted = 100 + (current_time.minute * 50) if current_time >= incident_start else 0
            cache_hit_rate = max(20, 95 - (current_time.minute * 2)) if current_time >= incident_start else 95
            
            # Service latency degradation (slow and steady)
            time_since_start = (current_time - incident_start).total_seconds() / 60  # minutes
            latency_multiplier = 1 + (time_since_start * 0.1)  # 10% increase per minute
            
            auth_latency = int(150 * latency_multiplier)
            products_latency = int(200 * latency_multiplier)
            checkout_latency = int(300 * latency_multiplier)
            
            # Database CPU increase
            db_cpu_base = 30
            db_cpu_increase = min(40, time_since_start * 2)  # Max 70% CPU
            
            auth_db_cpu = db_cpu_base + db_cpu_increase
            products_db_cpu = db_cpu_base + db_cpu_increase
            checkout_db_cpu = db_cpu_base + db_cpu_increase
        else:
            # Normal metrics
            cache_evicted = 0
            cache_hit_rate = 95 + (current_time.minute % 5)
            auth_latency = 150 + (current_time.minute % 50)
            products_latency = 200 + (current_time.minute % 50)
            checkout_latency = 300 + (current_time.minute % 50)
            auth_db_cpu = 30 + (current_time.minute % 20)
            products_db_cpu = 30 + (current_time.minute % 20)
            checkout_db_cpu = 30 + (current_time.minute % 20)
        
        metrics_data.append({
            "timestamp": timestamp,
            "caching_service.cache.evicted_keys": cache_evicted,
            "caching_service.cache.hit_rate": cache_hit_rate,
            "auth_service.p99_latency": auth_latency,
            "products_api.p99_latency": products_latency,
            "checkout_service.p99_latency": checkout_latency,
            "auth_db.cpu.utilization": auth_db_cpu,
            "products_db.cpu.utilization": products_db_cpu,
            "checkout_db.cpu.utilization": checkout_db_cpu
        })
        
        current_time += timedelta(minutes=1)
    
    save_metrics(metrics_path, metrics_data)
    print(f"Generated 'The Silent Killer Cache' incident data in: {incident_path}")


def generate_retry_storm_cascade_data(incident_dir: str):
    """Incident 4: The Retry Storm Cascade (High)"""
    incident_path, logs_path, metrics_path = create_incident_structure(incident_dir)
    
    # Incident timeline
    incident_start = datetime(2024, 1, 15, 14, 15, 0)  # 14:15 - Payment gateway issues
    incident_end = datetime(2024, 1, 15, 14, 55, 0)    # 14:55 - Resolution
    
    # Generate logs for services
    services = ["payment-gateway", "checkout-service", "auth-service"]
    
    for service in services:
        logs = []
        current_time = datetime(2024, 1, 15, 13, 0, 0)
        end_time = datetime(2024, 1, 15, 16, 0, 0)
        
        while current_time <= end_time:
            timestamp = current_time.isoformat()
            
            if service == "payment-gateway":
                if current_time >= incident_start and current_time <= incident_end:
                    # Intermittent failures
                    if current_time.minute % 3 == 0:  # Every 3 minutes
                        logs.append({
                            "timestamp": timestamp,
                            "level": "ERROR",
                            "service": service,
                            "message": "Upstream provider returned 503",
                            "http_status": 503,
                            "response_time": 5000 + (current_time.minute * 100)
                        })
                else:
                    # Normal operation
                    if current_time.minute % 10 == 0:  # Every 10 minutes
                        logs.append({
                            "timestamp": timestamp,
                            "level": "INFO",
                            "service": service,
                            "message": "Payment gateway operating normally",
                            "http_status": 200,
                            "response_time": 200 + (current_time.minute % 50)
                        })
            
            elif service == "checkout-service":
                if current_time >= incident_start and current_time <= incident_end:
                    # Retry storm logs
                    if current_time.minute % 1 == 0:  # Every minute
                        logs.append({
                            "timestamp": timestamp,
                            "level": "INFO",
                            "service": service,
                            "message": f"Payment failed, retrying (attempt {2 + (current_time.minute % 2)}/3)...",
                            "retry_count": 2 + (current_time.minute % 2),
                            "payment_id": f"pay_{current_time.minute:04d}"
                        })
                else:
                    # Normal operation
                    if current_time.minute % 10 == 0:  # Every 10 minutes
                        logs.append({
                            "timestamp": timestamp,
                            "level": "INFO",
                            "service": service,
                            "message": "Checkout service operating normally",
                            "http_status": 200,
                            "response_time": 300 + (current_time.minute % 50)
                        })
            
            elif service == "auth-service":
                if current_time >= incident_start and current_time <= incident_end:
                    # High load from retry storm
                    if current_time >= datetime(2024, 1, 15, 14, 20, 0):  # 5 minutes after incident start
                        if current_time.minute % 2 == 0:  # Every 2 minutes
                            logs.append({
                                "timestamp": timestamp,
                                "level": "ERROR",
                                "service": service,
                                "message": "High load, shedding requests",
                                "cpu_usage": 90 + (current_time.minute % 10),
                                "request_rate": 1000 + (current_time.minute * 100)
                            })
                else:
                    # Normal operation
                    if current_time.minute % 10 == 0:  # Every 10 minutes
                        logs.append({
                            "timestamp": timestamp,
                            "level": "INFO",
                            "service": service,
                            "message": "Auth service operating normally",
                            "cpu_usage": 30 + (current_time.minute % 20),
                            "request_rate": 100 + (current_time.minute % 50)
                        })
            
            current_time += timedelta(minutes=1)
        
        save_logs(logs_path, service, logs)
    
    # Generate metrics CSV
    metrics_data = []
    current_time = datetime(2024, 1, 15, 13, 0, 0)
    end_time = datetime(2024, 1, 15, 16, 0, 0)
    
    while current_time <= end_time:
        timestamp = current_time.isoformat()
        
        if current_time >= incident_start and current_time <= incident_end:
            # Payment gateway failures
            payment_failures = 30 + (current_time.minute % 20)  # ~30% failure rate
            
            # Checkout service CPU spike
            time_since_start = (current_time - incident_start).total_seconds() / 60
            checkout_cpu = min(95, 50 + (time_since_start * 10))  # Spike to 95%
            
            # Auth service CPU spike (delayed)
            if current_time >= datetime(2024, 1, 15, 14, 20, 0):
                auth_cpu = min(90, 40 + ((current_time - datetime(2024, 1, 15, 14, 20, 0)).total_seconds() / 60 * 10))
            else:
                auth_cpu = 30 + (current_time.minute % 20)
        else:
            # Normal metrics
            payment_failures = 1 + (current_time.minute % 3)
            checkout_cpu = 30 + (current_time.minute % 20)
            auth_cpu = 30 + (current_time.minute % 20)
        
        metrics_data.append({
            "timestamp": timestamp,
            "payment_gateway.http.errors.5xx": payment_failures,
            "checkout_service.cpu.utilization": checkout_cpu,
            "auth_service.cpu.utilization": auth_cpu
        })
        
        current_time += timedelta(minutes=1)
    
    save_metrics(metrics_path, metrics_data)
    print(f"Generated 'The Retry Storm Cascade' incident data in: {incident_path}")


def generate_phantom_dns_data(incident_dir: str):
    """Incident 5: The Phantom DNS (Very High)"""
    incident_path, logs_path, metrics_path = create_incident_structure(incident_dir)
    
    # Incident timeline
    incident_start = datetime(2024, 1, 15, 14, 0, 0)   # 14:00 - DNS issues start
    incident_end = datetime(2024, 1, 15, 16, 0, 0)     # 16:00 - Resolution
    
    # Generate logs for checkout-service (only service with DNS issues)
    logs = []
    current_time = datetime(2024, 1, 15, 13, 0, 0)
    end_time = datetime(2024, 1, 15, 17, 0, 0)
    
    # Track DNS errors to ensure they're scattered
    dns_error_minutes = set()
    if incident_start <= current_time <= incident_end:
        # Generate 1-2 DNS errors per minute during incident period
        for minute in range(incident_start.minute, incident_end.minute + 1):
            if random.random() < 0.3:  # 30% chance of error each minute
                dns_error_minutes.add(minute)
    
    while current_time <= end_time:
        timestamp = current_time.isoformat()
        
        # Normal operation logs (most of the time)
        if current_time.minute % 10 == 0:  # Every 10 minutes
            logs.append({
                "timestamp": timestamp,
                "level": "INFO",
                "service": "checkout-service",
                "message": "Checkout service operating normally",
                "http_status": 200,
                "response_time": 300 + (current_time.minute % 50),
                "checkout_success_rate": 99 + (current_time.minute % 1)
            })
        
        # Scattered DNS errors during incident
        if current_time >= incident_start and current_time <= incident_end:
            if current_time.minute in dns_error_minutes:
                logs.append({
                    "timestamp": timestamp,
                    "level": "ERROR",
                    "service": "checkout-service",
                    "message": random.choice([
                        "Could not resolve host: shipping-api.com",
                        "DNS resolution timed out for shipping-api.com",
                        "Failed to connect to shipping-api.com: Name or service not known"
                    ]),
                    "http_status": 503,
                    "response_time": 30000
                })
        
        current_time += timedelta(minutes=1)
    
    save_logs(logs_path, "checkout-service", logs)
    
    # Generate metrics CSV - all metrics look normal except business metric
    metrics_data = []
    current_time = datetime(2024, 1, 15, 13, 0, 0)
    end_time = datetime(2024, 1, 15, 17, 0, 0)
    
    while current_time <= end_time:
        timestamp = current_time.isoformat()
        
        # All service metrics look completely normal
        auth_cpu = 30 + (current_time.minute % 20)
        auth_memory = 45 + (current_time.minute % 25)
        checkout_cpu = 35 + (current_time.minute % 15)
        checkout_memory = 50 + (current_time.minute % 20)
        shipping_cpu = 25 + (current_time.minute % 15)
        
        # Only business metric shows the issue
        if current_time >= incident_start and current_time <= incident_end:
            # Small but steady increase in checkout failures
            time_since_start = (current_time - incident_start).total_seconds() / 60
            checkout_failures = int(5 + (time_since_start * 0.5))  # 5 failures + 0.5 per minute
        else:
            checkout_failures = 1 + (current_time.minute % 3)
        
        metrics_data.append({
            "timestamp": timestamp,
            "auth_service.cpu.utilization": auth_cpu,
            "auth_service.memory.usage": auth_memory,
            "checkout_service.cpu.utilization": checkout_cpu,
            "checkout_service.memory.usage": checkout_memory,
            "shipping_api.cpu.utilization": shipping_cpu,
            "checkout.failures.total": checkout_failures
        })
        
        current_time += timedelta(minutes=1)
    
    save_metrics(metrics_path, metrics_data)
    print(f"Generated 'The Phantom DNS' incident data in: {incident_path}")


def main(incident_name: str):
    """Main router function that generates incident data based on the incident name."""
    incident_generators = {
        'bad_deploy': generate_bad_deploy_data,
        'thundering_herd': generate_thundering_herd_data,
        'silent_cache_killer': generate_silent_cache_killer_data,
        'retry_storm_cascade': generate_retry_storm_cascade_data,
        'phantom_dns': generate_phantom_dns_data
    }
    
    if incident_name not in incident_generators:
        print(f"Error: Unknown incident '{incident_name}'")
        print("Available incidents:")
        for name in incident_generators.keys():
            print(f"  - {name}")
        return
    
    print(f"Generating incident data for: {incident_name}")
    incident_generators[incident_name](incident_name)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        incident_name = sys.argv[1]
        if incident_name == "all":
            print("Generating all incident scenarios...")
            incidents = ['bad_deploy', 'thundering_herd', 'silent_cache_killer', 'retry_storm_cascade', 'phantom_dns']
            for incident in incidents:
                print(f"\n--- Generating {incident} ---")
                main(incident)
            print("\nAll incidents generated successfully!")
        else:
            main(incident_name)
    else:
        print("Augur Data Generator - Generate realistic incident scenarios")
        print("=" * 60)
        print("Usage: python main.py <incident_name>")
        print("\nAvailable incidents:")
        print("  - bad_deploy           : Simple memory leak in auth-service")
        print("  - thundering_herd      : Traffic spike overwhelms database connections")
        print("  - silent_cache_killer  : Cache eviction causes slow degradation")
        print("  - retry_storm_cascade  : Payment failures trigger retry storm")
        print("  - phantom_dns          : Intermittent DNS issues cause scattered failures")
        print("  - all                  : Generate all scenarios")
        print("\nExamples:")
        print("  python main.py bad_deploy")
        print("  python main.py all") 