import json
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path


def generate_database_incident_data(incident_dir: str):
    """
    Generate realistic incident data for a database overload scenario.
    
    Scenario: A database connection pool gets exhausted due to a slow query,
    causing high latency and timeouts across multiple services.
    """
    
    # Create incident directory structure
    incident_path = Path("incidents") / incident_dir
    logs_path = incident_path / "logs"
    metrics_path = incident_path / "metrics"
    
    logs_path.mkdir(parents=True, exist_ok=True)
    metrics_path.mkdir(parents=True, exist_ok=True)
    
    # Incident timeline
    incident_start = datetime(2024, 1, 15, 16, 30, 0)  # 16:30 - Database issues start
    incident_end = datetime(2024, 1, 15, 17, 15, 0)   # 17:15 - Resolution
    
    # Generate logs for each service
    services = ["user-service", "order-service", "payment-service"]
    
    for service in services:
        logs = []
        
        # Generate logs for the entire day (15:00 to 18:00)
        current_time = datetime(2024, 1, 15, 15, 0, 0)
        end_time = datetime(2024, 1, 15, 18, 0, 0)
        
        while current_time <= end_time:
            timestamp = current_time.isoformat()
            
            if current_time >= incident_start and current_time <= incident_end:
                # During incident - database connection issues
                if current_time.minute % 3 == 0:  # Every 3 minutes
                    logs.append({
                        "timestamp": timestamp,
                        "level": "ERROR",
                        "service": service,
                        "message": f"Database connection timeout after 30s",
                        "db_connections": 95 + (current_time.minute % 5),
                        "response_time": 30000 + (current_time.minute * 1000)
                    })
                
                if current_time.minute % 5 == 0:  # Every 5 minutes
                    logs.append({
                        "timestamp": timestamp,
                        "level": "WARN",
                        "service": service,
                        "message": f"High database latency: {5000 + (current_time.minute * 100)}ms",
                        "db_latency": 5000 + (current_time.minute * 100),
                        "active_connections": 90 + (current_time.minute % 10)
                    })
            else:
                # Normal operation
                if current_time.minute % 10 == 0:  # Every 10 minutes
                    logs.append({
                        "timestamp": timestamp,
                        "level": "INFO",
                        "service": service,
                        "message": "Service operating normally",
                        "db_connections": 20 + (current_time.minute % 15),
                        "response_time": 150 + (current_time.minute % 50)
                    })
            
            current_time += timedelta(minutes=1)
        
        # Save logs to file
        log_file = logs_path / f"{service}.log"
        with open(log_file, 'w') as f:
            for log in logs:
                f.write(json.dumps(log) + '\n')
    
    # Generate metrics CSV
    metrics_data = []
    current_time = datetime(2024, 1, 15, 15, 0, 0)
    end_time = datetime(2024, 1, 15, 18, 0, 0)
    
    while current_time <= end_time:
        timestamp = current_time.isoformat()
        
        # Database metrics
        if current_time >= incident_start and current_time <= incident_end:
            db_connections = 95 + (current_time.minute % 5)
            db_latency = 5000 + (current_time.minute * 100)
            user_errors = 15 + (current_time.minute % 10)
            order_errors = 20 + (current_time.minute % 15)
            payment_errors = 25 + (current_time.minute % 20)
        else:
            db_connections = 20 + (current_time.minute % 15)
            db_latency = 50 + (current_time.minute % 30)
            user_errors = 1 + (current_time.minute % 3)
            order_errors = 1 + (current_time.minute % 2)
            payment_errors = 1 + (current_time.minute % 3)
        
        metrics_data.append({
            "timestamp": timestamp,
            "database.connections.active": db_connections,
            "database.query.latency_ms": db_latency,
            "user_service.http.errors.5xx": user_errors,
            "order_service.http.errors.5xx": order_errors,
            "payment_service.http.errors.5xx": payment_errors
        })
        
        current_time += timedelta(minutes=1)
    
    # Save metrics to CSV
    metrics_file = metrics_path / "metrics.csv"
    with open(metrics_file, 'w', newline='') as f:
        if metrics_data:
            writer = csv.DictWriter(f, fieldnames=metrics_data[0].keys())
            writer.writeheader()
            writer.writerows(metrics_data)
    
    print(f"Generated database incident data in: {incident_path}")
    print(f"Logs: {logs_path}")
    print(f"Metrics: {metrics_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        incident_name = sys.argv[1]
        generate_database_incident_data(incident_name)
    else:
        print("Usage: python database_incident.py <incident_name>") 