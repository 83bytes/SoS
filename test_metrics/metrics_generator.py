#!/usr/bin/env python3
"""
Custom Metrics Generator for Alert Testing

Generates various types of metrics (counters and gauges) with configurable patterns
to test different alert combinations and scenarios.
"""

import time
import random
import math
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from flask import Flask, Response, jsonify
from urllib.parse import urlparse
import threading
import signal
import sys


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"


class Pattern(Enum):
    STEADY = "steady"
    INCREASING = "increasing"
    DECREASING = "decreasing"
    SPIKY = "spiky"
    SINE_WAVE = "sine_wave"
    RANDOM_WALK = "random_walk"
    THRESHOLD_BREACH = "threshold_breach"


@dataclass
class MetricConfig:
    name: str
    metric_type: MetricType
    pattern: Pattern
    base_value: float
    amplitude: float = 10.0
    frequency: float = 1.0
    noise_level: float = 0.1
    labels: Optional[Dict[str, str]] = None


class MetricsGenerator:
    def __init__(self):
        self.start_time = time.time()
        self.step_count = 0
        self.metrics_state = {}
        self.configs = []
        self.output_format = "prometheus"

    def generate_value(self, config: MetricConfig) -> float:
        """Generate a metric value based on the configuration pattern."""
        current_time = time.time() - self.start_time

        if config.pattern == Pattern.STEADY:
            value = config.base_value

        elif config.pattern == Pattern.INCREASING:
            value = config.base_value + (current_time * config.frequency)

        elif config.pattern == Pattern.DECREASING:
            value = config.base_value - (current_time * config.frequency)

        elif config.pattern == Pattern.SPIKY:
            if random.random() < 0.1:  # 10% chance of spike
                value = config.base_value + config.amplitude * random.uniform(2, 5)
            else:
                value = config.base_value

        elif config.pattern == Pattern.SINE_WAVE:
            value = config.base_value + config.amplitude * math.sin(current_time * config.frequency)

        elif config.pattern == Pattern.RANDOM_WALK:
            if config.name not in self.metrics_state:
                self.metrics_state[config.name] = config.base_value

            change = random.uniform(-config.frequency, config.frequency)
            self.metrics_state[config.name] += change
            value = self.metrics_state[config.name]

        elif config.pattern == Pattern.THRESHOLD_BREACH:
            # Periodically breach a threshold
            cycle_time = current_time % 60  # 60 second cycle
            if 20 <= cycle_time <= 30:  # Breach for 10 seconds every minute
                value = config.base_value + config.amplitude * 2
            else:
                value = config.base_value

        # Add noise
        noise = random.uniform(-config.noise_level, config.noise_level) * config.amplitude
        value += noise

        # For counters, ensure monotonic increase
        if config.metric_type == MetricType.COUNTER:
            if config.name not in self.metrics_state:
                self.metrics_state[config.name] = max(0, value)
            else:
                # Counters should only increase
                value = max(self.metrics_state[config.name], self.metrics_state[config.name] + abs(value - config.base_value) * 0.1)
                self.metrics_state[config.name] = value

        return max(0, value)  # Ensure non-negative values

    def generate_metrics(self, configs: List[MetricConfig]) -> List[Dict[str, Any]]:
        """Generate metrics for all configurations."""
        timestamp = datetime.now().isoformat()
        metrics = []

        for config in configs:
            value = self.generate_value(config)

            metric = {
                "name": config.name,
                "type": config.metric_type.value,
                "value": round(value, 2),
                "timestamp": timestamp,
                "labels": config.labels or {}
            }
            metrics.append(metric)

        self.step_count += 1
        return metrics

    def set_configs(self, configs: List[MetricConfig]):
        """Set the metric configurations."""
        self.configs = configs

    def set_output_format(self, output_format: str):
        """Set the output format."""
        self.output_format = output_format

    def format_metrics_output(self, metrics: List[Dict[str, Any]]) -> str:
        """Format metrics in Prometheus format."""
        output_lines = []
        for metric in metrics:
            labels_str = ",".join([f'{k}="{v}"' for k, v in metric["labels"].items()])
            if labels_str:
                output_lines.append(f'{metric["name"]}{{{labels_str}}} {metric["value"]}')
            else:
                output_lines.append(f'{metric["name"]} {metric["value"]}')
        return "\n".join(output_lines)


def create_default_configs() -> List[MetricConfig]:
    """Create a set of default metric configurations for testing - predictable values with no randomness."""
    return [
        # HTTP Request Metrics
        MetricConfig("test_metrics_http_requests_total", MetricType.COUNTER, Pattern.STEADY, 1000, 0, 1.0, 0.0,
                    {"service": "api", "method": "GET"}),
        MetricConfig("test_metrics_http_requests_total", MetricType.COUNTER, Pattern.INCREASING, 500, 10, 1.0, 0.0,
                    {"service": "api", "method": "POST"}),
        MetricConfig("test_metrics_http_errors_total", MetricType.COUNTER, Pattern.STEADY, 5, 0, 1.0, 0.0,
                    {"service": "api", "status": "500"}),

        # System Metrics
        MetricConfig("test_metrics_cpu_usage_percent", MetricType.GAUGE, Pattern.STEADY, 50, 0, 1.0, 0.0),
        MetricConfig("test_metrics_memory_usage_percent", MetricType.GAUGE, Pattern.STEADY, 60, 0, 1.0, 0.0),
        MetricConfig("test_metrics_disk_usage_percent", MetricType.GAUGE, Pattern.INCREASING, 70, 1, 0.1, 0.0),

        # Application Metrics
        MetricConfig("test_metrics_queue_size", MetricType.GAUGE, Pattern.STEADY, 100, 0, 1.0, 0.0,
                    {"queue": "processing"}),
        MetricConfig("test_metrics_active_connections", MetricType.GAUGE, Pattern.STEADY, 500, 0, 1.0, 0.0),
        MetricConfig("test_metrics_response_time_ms", MetricType.GAUGE, Pattern.STEADY, 100, 0, 1.0, 0.0,
                    {"endpoint": "/api/users"}),

        # Database Metrics
        MetricConfig("test_metrics_db_connections_active", MetricType.GAUGE, Pattern.STEADY, 20, 0, 1.0, 0.0),
        MetricConfig("test_metrics_db_query_duration_ms", MetricType.GAUGE, Pattern.STEADY, 50, 0, 1.0, 0.0),
        MetricConfig("test_metrics_db_slow_queries_total", MetricType.COUNTER, Pattern.STEADY, 2, 0, 1.0, 0.0),
    ]


def create_flask_app(generator: MetricsGenerator) -> Flask:
    """Create Flask application with metrics endpoints."""
    app = Flask(__name__)

    @app.route('/metrics')
    def metrics():
        try:
            metrics_data = generator.generate_metrics(generator.configs)
            output = generator.format_metrics_output(metrics_data)
            return Response(output, mimetype='text/plain; charset=utf-8')
        except Exception as e:
            return Response(f"Internal Server Error: {str(e)}", status=500)

    @app.route('/')
    @app.route('/health')
    def health():
        health_data = {
            "status": "healthy",
            "metrics_count": len(generator.configs),
            "uptime_seconds": round(time.time() - generator.start_time, 2)
        }
        return jsonify(health_data)

    return app


def start_http_server(generator: MetricsGenerator, port: int, verbose: bool = False):
    """Start Flask HTTP server to serve metrics."""
    app = create_flask_app(generator)

    if verbose:
        print(f"Starting Flask server on port {port}")
        print(f"Metrics available at: http://localhost:{port}/metrics")
        print(f"Health check at: http://localhost:{port}/health")
        print("Press Ctrl+C to stop")

    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        if verbose:
            print("\nKeyboard interrupt received, shutting down...")
    except Exception as e:
        if verbose:
            print(f"Server error: {e}")
        raise
 



def main():
    parser = argparse.ArgumentParser(description="Generate custom metrics for alert testing")
    parser.add_argument("--port", "-p", type=int, default=8000,
                       help="Port for HTTP server")
    parser.add_argument("--config", "-c", type=str,
                       help="JSON file with custom metric configurations")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")

    args = parser.parse_args()

    # Load configurations
    if args.config:
        with open(args.config, 'r') as f:
            config_data = json.load(f)
            configs = [MetricConfig(**cfg) for cfg in config_data]
    else:
        configs = create_default_configs()

    generator = MetricsGenerator()
    generator.set_configs(configs)
    generator.set_output_format("prometheus")

    start_http_server(generator, args.port, args.verbose)


if __name__ == "__main__":
    main()