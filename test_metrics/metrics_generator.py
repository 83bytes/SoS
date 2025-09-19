#!/usr/bin/env python3
"""
Custom Metrics Generator for Alert Testing

Generates various types of metrics (counters and gauges) with configurable patterns
to test different alert combinations and scenarios.
"""

import os
import sys
import time
import random
import math
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from flask import Flask, Response, jsonify, request
from abc import ABC, abstractmethod
import csv
import io
from typing import Generator, Callable


# Custom Function Registry
CUSTOM_FUNCTIONS = {}

def register_custom_function(name: str, func: Callable) -> None:
    """Register a custom function for use in metric generation."""
    CUSTOM_FUNCTIONS[name] = func

def square_function(config: 'MetricConfig') -> Generator[float, None, None]:
    """Example custom function: yields i*i for i in range."""
    i = 1
    while True:
        yield float(i * i)
        i += 1

def power_function(config: 'MetricConfig') -> Generator[float, None, None]:
    """Example custom function: yields i**i for i in range."""
    i = 1
    while True:
        yield float(i ** i)
        i += 1

# Register example functions
register_custom_function("square", square_function)
register_custom_function("power", power_function)


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"



@dataclass
class MetricConfig:
    name: str
    metric_type: MetricType
    custom_function: str
    reset_interval: int = 1
    labels: Optional[Dict[str, str]] = None


class PatternIterator(ABC):
    """Base class for pattern iterators that generate metric values."""

    def __init__(self, config: MetricConfig, start_time: float):
        self.config = config
        self.start_time = start_time
        self.state = {}
        self.tick_count = 0

    @abstractmethod
    def __next__(self) -> float:
        """Generate the next value in the pattern."""
        pass

    def __iter__(self):
        return self


class CustomFunctionIterator(PatternIterator):
    """Iterator that uses custom registered functions to generate values."""

    def __init__(self, config: 'MetricConfig', start_time: float):
        super().__init__(config, start_time)
        function_name = getattr(config, 'custom_function', None)
        if function_name and function_name in CUSTOM_FUNCTIONS:
            self.generator = CUSTOM_FUNCTIONS[function_name](config)
        else:
            raise ValueError(f"Custom function '{function_name}' not found in registry")

    def __next__(self) -> float:
        self.tick_count += 1
        try:
            value = next(self.generator)
            return value
        except StopIteration:
            # something triggered the exit. lets exit
            sys.exit(0)

class MetricsGenerator:
    def __init__(self):
        self.start_time = time.time()
        self.step_count = 0
        self.configs = []
        self.iterators = {}
        self.output_format = "prometheus"

    def _initialize_iterators(self):
        """Initialize iterators for all configured metrics."""
        self.iterators = {}
        for config in self.configs:
            # Use custom function iterator
            self.iterators[config.name] = CustomFunctionIterator(config, self.start_time)

    def generate_value(self, config: MetricConfig) -> float:
        """Generate a metric value using the iterator-based approach."""
        
        # Get next value from iterator
        value = next(self.iterators[config.name])

        return value

    def generate_metrics(self, configs: List[MetricConfig]) -> List[Dict[str, Any]]:
        """Generate metrics for all configurations."""
        timestamp = datetime.now().isoformat()
        metrics = []

        for config in configs:
            value = self.generate_value(config)

            metric = {
                "name": f"test_metrics_{config.name}",
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
        self._initialize_iterators()

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
    """Create a set of default metric configurations for testing."""
    return [
        MetricConfig(
            name="custom_square",
            metric_type=MetricType.GAUGE,
            custom_function="square",
        ),
        MetricConfig(
            name="custom_power",
            metric_type=MetricType.GAUGE,
            custom_function="power",
        ),
    ]


def create_flask_app(generator: MetricsGenerator) -> Flask:
    """Create Flask application with metrics endpoints."""
    app = Flask(__name__)

    # Enable logging
    import logging
    if not app.debug:
        app.logger.setLevel(logging.INFO)

    @app.route('/metrics')
    def metrics():
        try:
            metrics_data = generator.generate_metrics(generator.configs)
            output = generator.format_metrics_output(metrics_data)
            return Response(output, mimetype='text/plain; charset=utf-8')
        except Exception as e:
            app.logger.error(f"Error generating metrics: {str(e)}", exc_info=True)
            return Response(f"Internal Server Error: {str(e)}", status=500)

    @app.route('/')
    @app.route('/health')
    def health():
        health_data = {
            "status": "healthy",
            "metrics_count": len(generator.configs),
            "uptime_seconds": round(time.time() - generator.start_time, 2),
            "total_ticks": generator.step_count,
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
        app.run(host='0.0.0.0', port=port, debug=verbose, use_reloader=False)
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
    config_file = args.config or 'example_config.json'

    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
            configs = []
            for cfg in config_data:
                # Convert string metric_type to enum
                if isinstance(cfg.get('metric_type'), str):
                    cfg['metric_type'] = MetricType(cfg['metric_type'])
                # Validate that custom_function is specified
                if not cfg.get('custom_function'):
                    raise ValueError(f"Config for '{cfg.get('name')}' must specify a custom_function")
                configs.append(MetricConfig(**cfg))
        if args.verbose:
            print(f"Loaded configuration from {config_file}")
    except FileNotFoundError:
        if args.verbose:
            print(f"Config file {config_file} not found, using hardcoded defaults")
        configs = create_default_configs()
    except json.JSONDecodeError as e:
        if args.verbose:
            print(f"Error parsing {config_file}: {e}, using hardcoded defaults")
        configs = create_default_configs()

    generator = MetricsGenerator()
    generator.set_configs(configs)
    generator.set_output_format("prometheus")

    start_http_server(generator, args.port, args.verbose)


if __name__ == "__main__":
    main()