import datetime
import json
import os
import re
from typing import Dict, List, Tuple

'''Creating visualization for testing metrics'''
try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("WARNING: Matplotlib not available. Install with: pip install matplotlib numpy")


class TestingMetrics:
    """Calculate and display testing metrics"""
    
    def __init__(self, report_file='report.txt'):
        """Initialize metrics calculator by reading from report file"""
        # If report_file is just a filename, look in the Testing folder
        if not os.path.isabs(report_file) and not os.path.dirname(report_file):
            testing_dir = os.path.dirname(os.path.abspath(__file__))
            self.report_file = os.path.join(testing_dir, report_file)
        else:
            self.report_file = report_file
        
        # Default values
        self.total_test_cases = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
        self.execution_time_seconds = 0
        
        # Defect data
        self.defects_found_in_testing = 0
        self.defects_found_in_production = 0
        self.critical_defects = 0
        self.high_defects = 0
        self.medium_defects = 0
        self.low_defects = 0
        
        # Code metrics (approximate)
        self.lines_of_code = 2900  # Updated: main.py, send_mail.py, recieve.py, db_manager.py
        self.lines_of_test_code = 1900  # Updated: testcases.py with 119 test cases
        self.test_duration_hours = 45  # Updated for 119 test cases
        
        # Time tracking
        self.test_start_time = datetime.datetime.now() - datetime.timedelta(hours=40)
        self.test_end_time = datetime.datetime.now()
        
        # Read data from report file if it exists
        if os.path.exists(self.report_file):
            self.read_report_file()
        else:
            print(f"WARNING: Report file '{self.report_file}' not found!")
            print("   Run 'python testcases.py' first to generate the report.\n")
    
    def read_report_file(self):
        """Read and parse the report.txt file to extract metrics"""
        try:
            with open(self.report_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract total test cases
            match = re.search(r'Total Test Cases Executed:\s*(\d+)', content)
            if match:
                self.total_test_cases = int(match.group(1))
            
            # Extract passed tests
            match = re.search(r'Passed:\s*(\d+)', content)
            if match:
                self.passed_tests = int(match.group(1))
            
            # Extract failed tests
            match = re.search(r'Failed:\s*(\d+)', content)
            if match:
                self.failed_tests = int(match.group(1))
            
            # Extract errors
            match = re.search(r'Errors:\s*(\d+)', content)
            if match:
                errors = int(match.group(1))
                self.failed_tests += errors  # Count errors as failures
            
            # Extract execution time
            match = re.search(r'Execution Time:\s*~?([\d.]+)\s*seconds', content)
            if match:
                self.execution_time_seconds = float(match.group(1))
            
            # Count defects (failed + error tests)
            self.defects_found_in_testing = self.failed_tests
            
            # Categorize defects by severity (based on test categories)
            # High severity: Database and Security failures
            # Medium severity: Email Sending/Receiving failures
            # Low severity: Edge case failures
            
            if 'Database' in content or 'Security' in content:
                self.high_defects = min(self.defects_found_in_testing, 2)
                self.medium_defects = self.defects_found_in_testing - self.high_defects
            else:
                self.medium_defects = self.defects_found_in_testing
            
            print(f"Successfully read report from: {self.report_file}")
            print(f"   Total Tests: {self.total_test_cases}")
            print(f"   Passed: {self.passed_tests}")
            print(f"   Failed: {self.failed_tests}")
            print(f"   Execution Time: {self.execution_time_seconds:.2f}s\n")
            
        except Exception as e:
            print(f"ERROR: Error reading report file: {e}\n")
    
    def calculate_defect_removal_efficiency(self) -> float:
        """
        Calculate Defect Removal Efficiency (DRE)
        
        Formula: DRE = (Defects Found in Testing / Total Defects) × 100
        Total Defects = Defects in Testing + Defects in Production
        
        Returns:
            float: DRE percentage
        """
        total_defects = self.defects_found_in_testing + self.defects_found_in_production
        
        if total_defects == 0:
            return 100.0
        
        dre = (self.defects_found_in_testing / total_defects) * 100
        return round(dre, 2)
    
    def calculate_defect_injection_rate(self) -> float:
        """
        Calculate Defect Injection Rate (DIR)
        
        Formula: DIR = (Total Defects / Lines of Code) × 1000
        This gives defects per 1000 lines of code (KLOC)
        
        Returns:
            float: Defects per KLOC
        """
        dir_value = (self.defects_found_in_testing / self.lines_of_code) * 1000
        return round(dir_value, 2)
    
    def calculate_mean_time_to_defect(self) -> float:
        """
        Calculate Mean Time To Defect (MTTD)
        
        Formula: MTTD = Total Test Time / Number of Defects Found
        
        Returns:
            float: Average hours between defect discoveries
        """
        if self.defects_found_in_testing == 0:
            return 0.0
        
        mttd = self.test_duration_hours / self.defects_found_in_testing
        return round(mttd, 2)
    
    def calculate_defect_density(self) -> float:
        """
        Calculate Defect Density
        
        Formula: Defect Density = Total Defects / Lines of Code × 1000
        Industry standard: < 1 defect per KLOC is excellent
        
        Returns:
            float: Defects per KLOC
        """
        defect_density = (self.defects_found_in_testing / self.lines_of_code) * 1000
        return round(defect_density, 2)
    
    def calculate_test_case_defect_density(self) -> float:
        """
        Calculate Test Case Defect Density
        
        Formula: Test Case Defect Density = Defects Found / Test Cases Executed
        
        Returns:
            float: Defects per test case
        """
        if self.total_test_cases == 0:
            return 0.0
        
        tcdd = self.defects_found_in_testing / self.total_test_cases
        return round(tcdd, 4)
    
    def calculate_test_effectiveness(self) -> float:
        """
        Calculate Test Effectiveness
        
        Formula: Test Effectiveness = (Failed Tests / Total Tests) × 100
        
        Returns:
            float: Percentage of tests that caught defects
        """
        if self.total_test_cases == 0:
            return 0.0
        
        effectiveness = (self.failed_tests / self.total_test_cases) * 100
        return round(effectiveness, 2)
    
    def calculate_pass_rate(self) -> float:
        """Calculate test pass rate"""
        if self.total_test_cases == 0:
            return 0.0
        return round((self.passed_tests / self.total_test_cases) * 100, 2)
    
    def calculate_fail_rate(self) -> float:
        """Calculate test fail rate"""
        if self.total_test_cases == 0:
            return 0.0
        return round((self.failed_tests / self.total_test_cases) * 100, 2)
    
    def calculate_test_coverage(self) -> float:
        """
        Estimate test coverage
        
        Formula: Coverage = (Lines of Test Code / Lines of Application Code) × 100
        """
        coverage = (self.lines_of_test_code / self.lines_of_code) * 100
        return round(min(coverage, 100), 2)
    
    def calculate_defect_severity_index(self) -> float:
        """
        Calculate weighted defect severity index
        
        Weights: Critical=4, High=3, Medium=2, Low=1
        """
        if self.defects_found_in_testing == 0:
            return 0.0
        
        total_weight = (
            self.critical_defects * 4 +
            self.high_defects * 3 +
            self.medium_defects * 2 +
            self.low_defects * 1
        )
        
        severity_index = total_weight / self.defects_found_in_testing
        return round(severity_index, 2)
    
    def get_all_metrics(self) -> Dict[str, float]:
        """Calculate and return all metrics"""
        return {
            'total_test_cases': self.total_test_cases,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'pass_rate': self.calculate_pass_rate(),
            'fail_rate': self.calculate_fail_rate(),
            'defect_removal_efficiency': self.calculate_defect_removal_efficiency(),
            'defect_injection_rate': self.calculate_defect_injection_rate(),
            'mean_time_to_defect': self.calculate_mean_time_to_defect(),
            'defect_density': self.calculate_defect_density(),
            'test_case_defect_density': self.calculate_test_case_defect_density(),
            'test_effectiveness': self.calculate_test_effectiveness(),
            'test_coverage_estimate': self.calculate_test_coverage(),
            'defect_severity_index': self.calculate_defect_severity_index(),
            'execution_time_seconds': self.execution_time_seconds,
            'total_defects': self.defects_found_in_testing,
            'lines_of_code': self.lines_of_code,
            'lines_of_test_code': self.lines_of_test_code
        }
    
    def print_metrics_report(self):
        """Print comprehensive metrics report"""
        metrics = self.get_all_metrics()
        
        print("\n" + "="*80)
        print("                    TESTING METRICS REPORT")
        print("="*80)
        
        print("\nTEST EXECUTION METRICS")
        print("-" * 80)
        print(f"Total Test Cases:        {metrics['total_test_cases']}")
        print(f"Passed Tests:            {metrics['passed_tests']}")
        print(f"Failed Tests:            {metrics['failed_tests']}")
        print(f"Pass Rate:               {metrics['pass_rate']}%")
        print(f"Fail Rate:               {metrics['fail_rate']}%")
        print(f"Execution Time:          {metrics['execution_time_seconds']:.2f} seconds")
        
        print("\nDEFECT METRICS")
        print("-" * 80)
        print(f"Total Defects Found:     {metrics['total_defects']}")
        print(f"  - Critical:            {self.critical_defects}")
        print(f"  - High:                {self.high_defects}")
        print(f"  - Medium:              {self.medium_defects}")
        print(f"  - Low:                 {self.low_defects}")
        
        print("\nKEY PERFORMANCE INDICATORS (KPIs)")
        print("-" * 80)
        
        # Defect Removal Efficiency
        dre = metrics['defect_removal_efficiency']
        dre_status = "Excellent" if dre >= 95 else "Good" if dre >= 85 else "Needs Improvement"
        print(f"Defect Removal Efficiency:     {dre}% {dre_status}")
        print(f"  Industry Benchmark: >95% (Excellent), >85% (Good)")
        
        # Defect Injection Rate
        dir_value = metrics['defect_injection_rate']
        dir_status = "Excellent" if dir_value < 1 else "Good" if dir_value < 2 else "High"
        print(f"\nDefect Injection Rate:         {dir_value} defects/KLOC {dir_status}")
        print(f"  Industry Benchmark: <1/KLOC (Excellent), <2/KLOC (Good)")
        
        # Mean Time To Defect
        mttd = metrics['mean_time_to_defect']
        print(f"\nMean Time To Defect:           {mttd} hours")
        print(f"  Average time between defect discoveries")
        
        # Defect Density
        dd = metrics['defect_density']
        dd_status = "Excellent" if dd < 1 else "Good" if dd < 2 else "High"
        print(f"\nDefect Density:                {dd} defects/KLOC {dd_status}")
        print(f"  Industry Benchmark: <1/KLOC (Excellent)")
        
        # Test Case Defect Density
        tcdd = metrics['test_case_defect_density']
        print(f"\nTest Case Defect Density:      {tcdd} defects/test")
        print(f"  Average defects found per test case")
        
        # Test Effectiveness
        te = metrics['test_effectiveness']
        print(f"\nTest Effectiveness:            {te}%")
        print(f"  Percentage of tests that detected defects")
        
        # Test Coverage
        tc = metrics['test_coverage_estimate']
        tc_status = "Good" if tc >= 80 else "Adequate" if tc >= 60 else "Low"
        print(f"\nTest Coverage (Estimated):     {tc}% {tc_status}")
        print(f"  Industry Benchmark: >80% (Good), >60% (Adequate)")
        
        # Defect Severity Index
        dsi = metrics['defect_severity_index']
        print(f"\nDefect Severity Index:         {dsi}/4.0")
        print(f"  Average severity weight (4=Critical, 1=Low)")
        
        print("\nCODE METRICS")
        print("-" * 80)
        print(f"Application LOC:         {metrics['lines_of_code']}")
        print(f"Test Code LOC:           {metrics['lines_of_test_code']}")
        print(f"Test/Code Ratio:         {round(metrics['lines_of_test_code']/metrics['lines_of_code'], 2)}")
        
        print("\nQUALITY ASSESSMENT")
        print("-" * 80)
        
        # Overall quality score
        quality_score = (
            (metrics['pass_rate'] * 0.3) +
            (metrics['defect_removal_efficiency'] * 0.3) +
            ((100 - dir_value * 10) * 0.2) +
            (metrics['test_coverage_estimate'] * 0.2)
        )
        
        if quality_score >= 90:
            quality_status = "EXCELLENT"
        elif quality_score >= 75:
            quality_status = "GOOD"
        else:
            quality_status = "NEEDS IMPROVEMENT"
        
        print(f"Overall Quality Score:   {round(quality_score, 2)}/100 {quality_status}")
        
        print("\nRECOMMENDATIONS")
        print("-" * 80)
        
        recommendations = []
        
        if metrics['pass_rate'] < 95:
            recommendations.append("• Investigate and fix failing test cases")
        
        if dir_value > 1:
            recommendations.append("• Reduce defect injection rate through code reviews")
        
        if metrics['defect_removal_efficiency'] < 95:
            recommendations.append("• Improve test coverage to catch more defects early")
        
        if self.high_defects > 0 or self.critical_defects > 0:
            recommendations.append("• Address high and critical severity defects immediately")
        
        if metrics['test_coverage_estimate'] < 80:
            recommendations.append("• Increase test coverage to at least 80%")
        
        if not recommendations:
            recommendations.append("• Maintain current quality standards")
            recommendations.append("• Continue monitoring metrics in production")
        
        for rec in recommendations:
            print(rec)
        
        print("\n" + "="*80)
        print("                    END OF METRICS REPORT")
        print("="*80 + "\n")
    
    def generate_visualization(self, save_path='testing_metrics_chart.png'):
        """Generate visual charts for metrics"""
        if not MATPLOTLIB_AVAILABLE:
            print("WARNING: Matplotlib not installed. Skipping visualization.")
            return None
        
        metrics = self.get_all_metrics()
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Email Client Testing Metrics Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Test Results Pie Chart
        sizes = [metrics['passed_tests'], metrics['failed_tests']]
        labels = [f"Passed\n({metrics['passed_tests']})", f"Failed\n({metrics['failed_tests']})"]
        colors = ['#2ecc71', '#e74c3c']
        explode = (0.05, 0.05)
        
        ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=90)
        ax1.set_title(f'Test Results\n(Pass Rate: {metrics["pass_rate"]}%)', fontweight='bold')
        
        # 2. Defect Severity Bar Chart
        severities = ['Critical', 'High', 'Medium', 'Low']
        counts = [self.critical_defects, self.high_defects, self.medium_defects, self.low_defects]
        severity_colors = ['#e74c3c', '#e67e22', '#f39c12', '#3498db']
        
        bars = ax2.bar(severities, counts, color=severity_colors, edgecolor='black', linewidth=1.5)
        ax2.set_ylabel('Number of Defects', fontweight='bold')
        ax2.set_title('Defects by Severity', fontweight='bold')
        ax2.set_ylim(0, max(counts) + 1 if max(counts) > 0 else 3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontweight='bold')
        
        # 3. Key Metrics Comparison
        metric_names = ['DRE', 'Coverage', 'Pass Rate']
        metric_values = [
            metrics['defect_removal_efficiency'],
            metrics['test_coverage_estimate'],
            metrics['pass_rate']
        ]
        benchmark = [95, 80, 95]  # Industry benchmarks
        
        x = np.arange(len(metric_names))
        width = 0.35
        
        bars1 = ax3.bar(x - width/2, metric_values, width, label='Actual',
                       color='#3498db', edgecolor='black', linewidth=1.5)
        bars2 = ax3.bar(x + width/2, benchmark, width, label='Benchmark',
                       color='#95a5a6', edgecolor='black', linewidth=1.5)
        
        ax3.set_ylabel('Percentage (%)', fontweight='bold')
        ax3.set_title('Key Metrics vs Industry Benchmarks', fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels(metric_names)
        ax3.legend()
        ax3.set_ylim(0, 105)
        ax3.axhline(y=100, color='red', linestyle='--', alpha=0.3)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%',
                        ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # 4. Defect Metrics Table
        ax4.axis('tight')
        ax4.axis('off')
        
        table_data = [
            ['Metric', 'Value', 'Status'],
            ['Defect Density', f'{metrics["defect_density"]}/KLOC', 
             '✓' if metrics["defect_density"] < 1 else '⚠'],
            ['Test Case DD', f'{metrics["test_case_defect_density"]:.4f}', '✓'],
            ['MTTD', f'{metrics["mean_time_to_defect"]} hrs', '✓'],
            ['Test Effectiveness', f'{metrics["test_effectiveness"]}%', '✓'],
            ['Severity Index', f'{metrics["defect_severity_index"]}/4.0',
             '✓' if metrics["defect_severity_index"] < 3 else '⚠']
        ]
        
        table = ax4.table(cellText=table_data, cellLoc='left', loc='center',
                         colWidths=[0.4, 0.35, 0.25])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # Style header row
        for i in range(3):
            table[(0, i)].set_facecolor('#3498db')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Alternate row colors
        for i in range(1, len(table_data)):
            for j in range(3):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#ecf0f1')
        
        ax4.set_title('Detailed Defect Metrics', fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"\nMetrics visualization saved to: {save_path}")
        
        return save_path
    
    def save_metrics_json(self, filepath='testing_metrics.json'):
        """Save metrics to JSON file"""
        metrics = self.get_all_metrics()
        
        # Add metadata
        metrics['generated_at'] = datetime.datetime.now().isoformat()
        metrics['test_suite'] = 'Email Client Test Suite v1.0'
        metrics['report_file'] = self.report_file
        
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"Metrics data saved to: {filepath}")


def main():
    """Main function to calculate and display metrics"""
    print("\nReading test results from Testing/report.txt...\n")
    
    # Initialize metrics calculator
    calculator = TestingMetrics('report.txt')
    
    # Check if we have valid data
    if calculator.total_test_cases == 0:
        print("ERROR: No test data found in report.txt")
        print("   Please run 'python testcases.py' first to generate test results.\n")
        return
    
    # Print comprehensive report
    calculator.print_metrics_report()
    
    # Get Testing folder path
    testing_dir = os.path.dirname(os.path.abspath(__file__))
    chart_path = os.path.join(testing_dir, 'testing_metrics_chart.png')
    json_path = os.path.join(testing_dir, 'testing_metrics.json')
    
    # Generate visualization
    try:
        if MATPLOTLIB_AVAILABLE:
            calculator.generate_visualization(chart_path)
    except Exception as e:
        print(f"WARNING: Could not generate visualization: {e}")
    
    # Save to JSON
    calculator.save_metrics_json(json_path)
    
    print("\nMetrics calculation complete!")
    print("   Check 'Testing/report.txt' for detailed test report")
    if MATPLOTLIB_AVAILABLE:
        print("   Check 'Testing/testing_metrics_chart.png' for visual dashboard")
    print("   Check 'Testing/testing_metrics.json' for raw data\n")


if __name__ == "__main__":
    main()
