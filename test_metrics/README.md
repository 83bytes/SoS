# Metrics Generator for Alert Testing

A Python-based HTTP server that generates synthetic metrics with configurable patterns to test different alert combinations and monitoring scenarios. Perfect for testing Prometheus alerting rules, Grafana dashboards, and monitoring system configurations.

## Features

- **HTTP Metrics Endpoint**: Serves Prometheus-format metrics at `/metrics`
- **On-Demand Generation**: Metrics generated fresh on each scrape request
- **Multiple Patterns**: 7 different metric behavior patterns (steady, increasing, spiky, etc.)
- **Realistic Metrics**: Pre-configured with common application and system metrics
- **Custom Configuration**: JSON-based configuration for custom metrics
- **Kubernetes Ready**: Includes deployment manifests and ServiceMonitor

## Quick Start

### Local Development

```bash
# Start the metrics server
python3 metrics_generator.py --port 8000 --verbose

# Scrape metrics
curl http://localhost:8000/metrics

# Check health
curl http://localhost:8000/health
```

### With Custom Configuration

```bash
# Using custom metrics configuration
python3 metrics_generator.py --config example_config.json --port 8080
```

## Metric Patterns

The generator supports 7 different patterns to simulate various system behaviors:

| Pattern | Description | Use Case |
|---------|-------------|----------|
| `steady` | Constant value with minor noise | Baseline metrics, stable systems |
| `increasing` | Linear growth over time | Growing load, memory leaks |
| `decreasing` | Linear decline over time | Decreasing capacity, cleanup processes |
| `spiky` | Random spikes with 10% probability | Intermittent errors, traffic bursts |
| `sine_wave` | Sinusoidal oscillation | Cyclical patterns, daily/weekly trends |
| `random_walk` | Random walk with drift | Unpredictable but bounded metrics |
| `threshold_breach` | Periodic threshold violations | Testing alert thresholds |

## Default Metrics

The generator comes with 12 pre-configured metrics:

### HTTP Metrics
- `http_requests_total{service="api",method="GET"}` - Increasing counter
- `http_requests_total{service="api",method="POST"}` - Spiky counter
- `http_errors_total{service="api",status="500"}` - Threshold breach counter

### System Metrics
- `cpu_usage_percent` - Sine wave gauge (0-100%)
- `memory_usage_percent` - Random walk gauge
- `disk_usage_percent` - Slowly increasing gauge

### Application Metrics
- `queue_size{queue="processing"}` - Spiky gauge
- `active_connections` - Sine wave gauge
- `response_time_ms{endpoint="/api/users"}` - Threshold breach gauge

### Database Metrics
- `db_connections_active` - Random walk gauge
- `db_query_duration_ms` - Spiky gauge
- `db_slow_queries_total` - Threshold breach counter

## Configuration

### Custom Metrics Configuration

Create a JSON file with custom metric configurations:

```json
[
  {
    "name": "custom_metric",
    "metric_type": "gauge",
    "pattern": "sine_wave",
    "base_value": 50.0,
    "amplitude": 20.0,
    "frequency": 0.1,
    "noise_level": 0.05,
    "labels": {
      "service": "custom",
      "environment": "test"
    }
  }
]
```

### Configuration Parameters

- `name`: Metric name (string)
- `metric_type`: "counter" or "gauge"
- `pattern`: One of the 7 supported patterns
- `base_value`: Base/starting value (float)
- `amplitude`: Pattern amplitude/range (float)
- `frequency`: Pattern frequency/speed (float)
- `noise_level`: Random noise level (0.0-1.0)
- `labels`: Optional metric labels (dict)

## Command Line Options

```
python3 metrics_generator.py [OPTIONS]

Options:
  --port, -p PORT        Port for HTTP server (default: 8000)
  --config, -c FILE      JSON file with custom metric configurations
  --verbose, -v          Verbose output
  --help, -h             Show help message
```

## Kubernetes Deployment

### Deploy with Kubectl
This deploys the application, the config-map and the servicemonitor 

```bash
# Deploy the metrics generator
kubectl apply -f k8s/

# Port forward for local access
kubectl port-forward deployment/metrics-generator 8000:8000

# Test metrics endpoint
curl http://localhost:8000/metrics
```

### Prometheus Integration

The deployment includes a ServiceMonitor for automatic Prometheus discovery:

```bash
# Apply the ServiceMonitor (requires Prometheus Operator)
kubectl apply -f k8s/servicemonitor.yaml
```

## Docker

### Build Image

```bash
# Build the container image
podman build -t metrics-generator .

# Run locally
podman run -p 8000:8000 metrics-generator
```

### Environment Variables

- `PORT`: Server port (default: 8000)
- `CONFIG_FILE`: Path to custom configuration file

## Monitoring Integration

### Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'metrics-generator'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 15s
```

### Grafana Dashboard

Import the provided Grafana dashboard (`grafana-dashboard.json`) to visualize the generated metrics.

### Example Alert Rules

```yaml
groups:
  - name: metrics-generator-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"

      - alert: HighCPUUsage
        expr: cpu_usage_percent > 80
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "CPU usage above 80%"
```

## Use Cases

### Alert Testing
- Test alert thresholds and timing
- Validate alert routing and notifications
- Simulate incident scenarios

### Dashboard Development
- Create and test Grafana dashboards
- Validate metric visualizations
- Test different time ranges and aggregations

### Load Testing
- Generate predictable metric patterns
- Test monitoring system performance
- Validate metric ingestion rates

### Training and Demos
- Demonstrate monitoring concepts
- Train teams on alert management
- Show metric pattern recognition

## Development

### Requirements
- Python 3.7+
- No external dependencies (uses only standard library)

### Testing
```bash
# Run basic functionality test
python3 -c "
import requests
import time
import subprocess

# Start server in background
proc = subprocess.Popen(['python3', 'metrics_generator.py', '--port', '9999'])
time.sleep(2)

# Test endpoints
print('Testing /metrics:', requests.get('http://localhost:9999/metrics').status_code)
print('Testing /health:', requests.get('http://localhost:9999/health').status_code)

# Cleanup
proc.terminate()
"
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   python3 metrics_generator.py --port 8001
   ```

2. **Custom config not loading**
   ```bash
   # Check JSON syntax
   python3 -m json.tool example_config.json
   ```

3. **Metrics not changing**
   - Each request to `/metrics` generates new values
   - Some patterns (like `steady`) have minimal variation

### Health Check

```bash
# Check if server is running
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "metrics_count": 12, "uptime_seconds": 45.2}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.