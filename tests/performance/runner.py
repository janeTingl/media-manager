"""Performance test runner and utilities."""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import pytest
import psutil


class PerformanceTestRunner:
    """Runner for performance tests with reporting."""
    
    def __init__(self, test_dir: Optional[Path] = None):
        """Initialize performance test runner.
        
        Args:
            test_dir: Directory containing performance tests
        """
        self.test_dir = test_dir or Path(__file__).parent
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
    
    def run_all_benchmarks(
        self, 
        output_file: Optional[str] = None,
        save_history: bool = True,
        compare_to_baseline: bool = True
    ) -> subprocess.CompletedProcess:
        """Run all performance benchmarks.
        
        Args:
            output_file: File to save benchmark results
            save_history: Whether to save results to history
            compare_to_baseline: Whether to compare with baseline results
            
        Returns:
            Subprocess result
        """
        # Prepare pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "-m", "benchmark",
            "--benchmark-only",
            "--benchmark-json", 
            str(self.results_dir / "latest_benchmark.json"),
            "--benchmark-sort", "min",
            "--benchmark-warmup", "on",
            "--benchmark-warmup-iterations", "3",
            "-v",
            "-p", "no:pytest-qt"  # Exclude Qt plugin to avoid display issues
        ]
        
        if output_file:
            cmd.extend(["--benchmark-save", output_file])
        
        # Run benchmarks
        print(f"Running performance benchmarks: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if save_history:
            self._save_to_history(result)
        
        if compare_to_baseline:
            self._compare_with_baseline()
        
        return result
    
    def run_specific_suite(
        self, 
        suite: str,
        output_file: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        """Run a specific benchmark suite.
        
        Args:
            suite: Suite name (database, scanning, ui, matching)
            output_file: File to save benchmark results
            
        Returns:
            Subprocess result
        """
        suite_file = self.test_dir / f"test_{suite}_performance.py"
        if not suite_file.exists():
            raise FileNotFoundError(f"Benchmark suite not found: {suite_file}")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(suite_file),
            "-m", "benchmark",
            "--benchmark-only",
            "--benchmark-json",
            str(self.results_dir / f"{suite}_benchmark.json"),
            "--benchmark-sort", "min",
            "-v",
            "-p", "no:pytest-qt"  # Exclude Qt plugin to avoid display issues
        ]
        
        if output_file:
            cmd.extend(["--benchmark-save", output_file])
        
        print(f"Running {suite} benchmarks: {' '.join(cmd)}")
        return subprocess.run(cmd, capture_output=True, text=True)
    
    def generate_report(self, json_file: Optional[str] = None) -> str:
        """Generate performance report from benchmark results.
        
        Args:
            json_file: JSON benchmark results file
            
        Returns:
            Report text
        """
        import json
        
        if json_file is None:
            json_file = self.results_dir / "latest_benchmark.json"
        
        if not Path(json_file).exists():
            return "No benchmark results found. Run benchmarks first."
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        report_lines = [
            "# Performance Benchmark Report",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"Total Benchmarks: {len(data.get('benchmarks', []))}",
            f"Machine: {data.get('machine_info', {}).get('system', 'Unknown')}",
            f"Python: {data.get('machine_info', {}).get('python_version', 'Unknown')}",
            "",
            "## Benchmark Results",
            ""
        ]
        
        benchmarks = data.get('benchmarks', [])
        
        # Group by test file
        grouped = {}
        for benchmark in benchmarks:
            test_file = benchmark.get('group', 'Unknown')
            if test_file not in grouped:
                grouped[test_file] = []
            grouped[test_file].append(benchmark)
        
        for test_file, file_benchmarks in grouped.items():
            report_lines.append(f"### {test_file}")
            report_lines.append("")
            
            for benchmark in file_benchmarks:
                name = benchmark.get('name', 'Unknown')
                min_time = benchmark.get('stats', {}).get('min', 0)
                max_time = benchmark.get('stats', {}).get('max', 0)
                mean_time = benchmark.get('stats', {}).get('mean', 0)
                std_dev = benchmark.get('stats', {}).get('stddev', 0)
                rounds = benchmark.get('stats', {}).get('rounds', 0)
                
                report_lines.extend([
                    f"**{name}**",
                    f"- Min: {min_time:.6f}s",
                    f"- Max: {max_time:.6f}s", 
                    f"- Mean: {mean_time:.6f}s",
                    f"- Std Dev: {std_dev:.6f}s",
                    f"- Rounds: {rounds}",
                    ""
                ])
        
        # Performance warnings
        report_lines.extend([
            "## Performance Analysis",
            ""
        ])
        
        # Check for slow operations
        slow_thresholds = {
            'db_search': 0.5,
            'ui_initial_load': 1.0,
            'ui_fetch_more': 0.5,
            'scan_per_item': 0.01,
            'match_per_item': 0.05
        }
        
        warnings = []
        for benchmark in benchmarks:
            name = benchmark.get('name', '')
            min_time = benchmark.get('stats', {}).get('min', 0)
            
            for threshold_name, threshold_value in slow_thresholds.items():
                if threshold_name in name and min_time > threshold_value:
                    warnings.append(
                        f"⚠️  {name}: {min_time:.3f}s (threshold: {threshold_value}s)"
                    )
        
        if warnings:
            report_lines.extend(["**Performance Warnings:**", ""])
            report_lines.extend(warnings)
        else:
            report_lines.append("✅ All benchmarks within performance thresholds")
        
        report_lines.extend([
            "",
            "## System Information",
            ""
        ])
        
        machine_info = data.get('machine_info', {})
        report_lines.extend([
            f"**CPU:** {machine_info.get('cpu', {}).get('brand', 'Unknown')}",
            f"**Cores:** {machine_info.get('cpu', {}).get('count', 'Unknown')}",
            f"**Memory:** {machine_info.get('mem', {}).get('total', 'Unknown')}",
            f"**OS:** {machine_info.get('system', 'Unknown')}",
            ""
        ])
        
        return "\n".join(report_lines)
    
    def _save_to_history(self, result: subprocess.CompletedProcess) -> None:
        """Save benchmark results to history.
        
        Args:
            result: Subprocess result from benchmark run
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        history_file = self.results_dir / f"benchmark_{timestamp}.txt"
        
        with open(history_file, 'w') as f:
            f.write(f"# Performance Benchmark Results\n")
            f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Return Code: {result.returncode}\n")
            f.write("\n## STDOUT\n")
            f.write(result.stdout)
            f.write("\n## STDERR\n")
            f.write(result.stderr)
        
        print(f"Benchmark results saved to: {history_file}")
    
    def _compare_with_baseline(self) -> None:
        """Compare latest results with baseline."""
        latest_file = self.results_dir / "latest_benchmark.json"
        baseline_file = self.results_dir / "baseline_benchmark.json"
        
        if not latest_file.exists():
            print("No latest benchmark results to compare")
            return
        
        if not baseline_file.exists():
            print("No baseline benchmark results found")
            return
        
        try:
            import json
            
            with open(latest_file, 'r') as f:
                latest_data = json.load(f)
            
            with open(baseline_file, 'r') as f:
                baseline_data = json.load(f)
            
            # Compare benchmarks
            latest_benchmarks = {b['name']: b for b in latest_data.get('benchmarks', [])}
            baseline_benchmarks = {b['name']: b for b in baseline_data.get('benchmarks', [])}
            
            regressions = []
            improvements = []
            
            for name, latest_benchmark in latest_benchmarks.items():
                if name in baseline_benchmarks:
                    baseline_benchmark = baseline_benchmarks[name]
                    
                    latest_min = latest_benchmark.get('stats', {}).get('min', 0)
                    baseline_min = baseline_benchmark.get('stats', {}).get('min', 0)
                    
                    if baseline_min > 0:
                        change_percent = ((latest_min - baseline_min) / baseline_min) * 100
                        
                        if change_percent > 10:  # 10% regression threshold
                            regressions.append(f"{name}: +{change_percent:.1f}%")
                        elif change_percent < -5:  # 5% improvement threshold
                            improvements.append(f"{name}: {change_percent:.1f}%")
            
            if regressions:
                print("⚠️  Performance Regressions Detected:")
                for regression in regressions:
                    print(f"  - {regression}")
            
            if improvements:
                print("🚀 Performance Improvements:")
                for improvement in improvements:
                    print(f"  - {improvement}")
            
            if not regressions and not improvements:
                print("✅ No significant performance changes detected")
                
        except Exception as e:
            print(f"Error comparing with baseline: {e}")
    
    def set_baseline(self, json_file: Optional[str] = None) -> None:
        """Set current results as performance baseline.
        
        Args:
            json_file: JSON file to use as baseline
        """
        if json_file is None:
            json_file = self.results_dir / "latest_benchmark.json"
        
        if not Path(json_file).exists():
            raise FileNotFoundError(f"Benchmark results not found: {json_file}")
        
        import shutil
        baseline_file = self.results_dir / "baseline_benchmark.json"
        shutil.copy2(json_file, baseline_file)
        print(f"Performance baseline set to: {baseline_file}")
    
    def check_system_resources(self) -> Dict[str, float]:
        """Check current system resource usage.
        
        Returns:
            Dictionary with resource usage info
        """
        process = psutil.Process()
        
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': process.memory_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'disk_usage_percent': psutil.disk_usage('/').percent
        }


def main():
    """Main entry point for performance test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Test Runner")
    parser.add_argument(
        "--suite", 
        choices=["database", "scanning", "ui", "matching"],
        help="Run specific benchmark suite"
    )
    parser.add_argument(
        "--output", 
        help="Output file for benchmark results"
    )
    parser.add_argument(
        "--report", 
        action="store_true",
        help="Generate performance report"
    )
    parser.add_argument(
        "--set-baseline", 
        action="store_true",
        help="Set current results as baseline"
    )
    parser.add_argument(
        "--no-history", 
        action="store_true",
        help="Don't save results to history"
    )
    parser.add_argument(
        "--no-compare", 
        action="store_true",
        help="Don't compare with baseline"
    )
    
    args = parser.parse_args()
    
    runner = PerformanceTestRunner()
    
    # Check system resources
    resources = runner.check_system_resources()
    print(f"System Resources: CPU: {resources['cpu_percent']:.1f}%, "
          f"Memory: {resources['memory_mb']:.1f}MB ({resources['memory_percent']:.1f}%)")
    
    if args.suite:
        result = runner.run_specific_suite(args.suite, args.output)
    else:
        result = runner.run_all_benchmarks(
            output_file=args.output,
            save_history=not args.no_history,
            compare_to_baseline=not args.no_compare
        )
    
    if result.returncode != 0:
        print(f"Benchmarks failed with return code: {result.returncode}")
        print("STDERR:", result.stderr)
        return 1
    
    if args.report:
        report = runner.generate_report()
        report_file = runner.results_dir / "performance_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"Performance report generated: {report_file}")
        print(report)
    
    if args.set_baseline:
        runner.set_baseline()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())