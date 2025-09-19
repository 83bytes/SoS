# Custom Metrics Generator

A Python-based metrics generator that creates custom metric patterns using user-defined iterator functions. Generate mathematical sequences like i*i, i**i, or any custom function and expose them as Prometheus metrics.

## Overview

This system allows you to:
- Define custom mathematical functions as Python generators
- Reference functions by name in JSON configuration
- Generate metrics at a one-minute interval
- Deploy via Docker/Podman and Kubernetes

## Architecture

### Core Components

- **Custom Function Registry**: Maps function names to Python generators
- **MetricConfig**: Configuration specifying function name and metric properties
- **CustomFunctionIterator**: Wraps generators to integrate with metrics system

### Example Functions

```python
def square_function(config: MetricConfig) -> Generator[float, None, None]:
    """yields i*i: 1, 4, 9, 16, 25..."""
    i = 1
    while True:
        yield float(i * i)
        i += 1

def power_function(config: MetricConfig) -> Generator[float, None, None]:
    """yields i**i: 1, 4, 27, 256..."""
    i = 1
    while True:
        yield float(i ** i)
        i += 1
```

## Configuration

### JSON Configuration Format

```json
[
  {
    "name": "custom_square",
    "metric_type": "gauge",
    "custom_function": "square"
  },
  {
    "name": "custom_power",
    "metric_type": "gauge",
    "custom_function": "power"
  }
]
```

### Required Fields
- `name`: Metric identifier
- `metric_type`: "gauge" or "counter"
- `custom_function`: Name of registered function

### Optional Fields
- `reset_interval`: Reset interval (default: 1)
- `labels`: Dictionary of Prometheus labels

## Usage

### Running Locally

```bash
# Install dependencies
make install

# Run with example config
make run-config

# Run with custom config
python3 metrics_generator.py --config your_config.json --port 8000 --verbose
```

### API Endpoints

#### `/metrics` - Generate Metrics
Returns current metric values in Prometheus format. New values are generated every minute.

```bash
curl http://localhost:8000/metrics
```

Example output:
```
test_metrics_custom_square 1
test_metrics_custom_power 1
```

After second call:
```
test_metrics_custom_square 4
test_metrics_custom_power 4
```

#### `/health` - Health Check
Returns service status and statistics.

```bash
curl http://localhost:8000/health
```

## Adding Custom Functions

### 1. Define Your Function

```python
def fibonacci_function(config: MetricConfig) -> Generator[float, None, None]:
    """Fibonacci sequence: 1, 1, 2, 3, 5, 8, 13..."""
    a, b = 1, 1
    while True:
        yield float(a)
        a, b = b, a + b

def exponential_function(config: MetricConfig) -> Generator[float, None, None]:
    """2^i: 2, 4, 8, 16, 32..."""
    i = 1
    while True:
        yield float(2 ** i)
        i += 1
```

### 2. Register Your Function

```python
register_custom_function("fibonacci", fibonacci_function)
register_custom_function("exponential", exponential_function)
```

### 3. Use in Configuration

```json
{
  "name": "my_fibonacci",
  "metric_type": "gauge",
  "custom_function": "fibonacci"
}
```

## Docker/Podman Deployment

### Build and Run

```bash
# Build image
make build

# Run container
podman run -p 8000:8000 test-metrics:latest

# Push to registry
make push
```

### Custom Configuration

```bash
# Run with custom config file
podman run -p 8000:8000 -v /path/to/config.json:/app/config.json test-metrics:latest --config config.json
```

## Kubernetes Deployment

```bash
# Deploy to cluster
make deploy

# Check status
make status

# View logs
make logs

# Port forward for local access
make port-forward

# Clean up
make undeploy
```

## Development

### Project Structure

```
├── metrics_generator.py    # Main application
├── example_config.json    # Example configuration
├── GAMEPLAN.md           # Development plan
├── Dockerfile            # Container build
├── Makefile             # Build commands
└── k8s/                 # Kubernetes manifests
```

### Testing

```bash
# Syntax check
make lint

# Run tests
make test

# Check health
make health

# Fetch current metrics
make metrics
```

## Design Philosophy

### Why Iterator Wrapper Pattern?

The system uses a two-level design:
1. **Custom Functions**: Pure generators defining mathematical sequences
2. **CustomFunctionIterator**: Wrapper handling integration with metrics system

This provides:
- **Separation of Concerns**: Math logic separate from metrics infrastructure
- **Flexibility**: Easy to add transformations, error handling, state management
- **Extensibility**: Framework for future features without changing core functions
- **Consistency**: All iterators implement the same interface

### Benefits

- **Pure Functions**: Mathematical generators are simple and testable
- **Composability**: Easy to combine and extend functions
- **Predictable**: Tick-based generation ensures reproducible sequences
- **Observable**: Full history tracking for analysis and debugging

## Troubleshooting

### Common Issues

1. **Function Not Found**: Ensure custom function is registered in `CUSTOM_FUNCTIONS`
2. **Config Validation**: All configs must specify `custom_function` field
3. **Port Conflicts**: Change port with `--port` or in Makefile
4. **Container Issues**: Check logs with `make logs` or `podman logs`

### Debugging

```bash
# Verbose output
python3 metrics_generator.py --verbose

# Check registered functions
python3 -c "from metrics_generator import CUSTOM_FUNCTIONS; print(list(CUSTOM_FUNCTIONS.keys()))"

# Validate config
python3 -c "import json; print(json.load(open('example_config.json')))"
```

## Contributing

1. Add new functions to the registry
2. Update example configurations
3. Add tests for new functionality
4. Update documentation
