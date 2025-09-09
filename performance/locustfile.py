"""
Performance testing configuration with load testing scripts and performance benchmarks.
"""

from locust import HttpUser, task, between
import random
import json


class AIWriterProUser(HttpUser):
    """Simulate user behavior for AI Writer PRO application."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts."""
        self.login()
    
    def login(self):
        """Login as a test user."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def view_dashboard(self):
        """View dashboard page."""
        self.client.get("/api/v1/users/me", headers=self.headers)
        self.client.get("/api/v1/organizations/", headers=self.headers)
    
    @task(2)
    def view_content_list(self):
        """View content list."""
        self.client.get("/api/v1/content/", headers=self.headers)
    
    @task(2)
    def view_style_profiles(self):
        """View style profiles."""
        self.client.get("/api/v1/styles/", headers=self.headers)
    
    @task(1)
    def create_style_profile(self):
        """Create a new style profile."""
        style_data = {
            "name": f"Test Style {random.randint(1, 1000)}",
            "description": "A test style profile for performance testing",
            "tone": random.choice(["professional", "casual", "friendly", "authoritative"]),
            "voice": random.choice(["first-person", "second-person", "third-person"]),
            "target_audience": random.choice(["general", "business", "academic", "technical"]),
            "content_type": random.choice(["article", "blog", "social", "email"])
        }
        
        self.client.post("/api/v1/styles/", 
                        json=style_data, 
                        headers=self.headers)
    
    @task(1)
    def generate_content(self):
        """Generate content."""
        content_data = {
            "title": f"Test Article {random.randint(1, 1000)}",
            "brief": "This is a test brief for content generation performance testing.",
            "target_words": random.randint(500, 2000),
            "style_profile_id": "1"  # Assuming style profile exists
        }
        
        self.client.post("/api/v1/content/generate", 
                        json=content_data, 
                        headers=self.headers)
    
    @task(1)
    def upload_file(self):
        """Upload a file."""
        # Create a small test file
        test_content = "This is a test file for performance testing."
        
        files = {
            "file": ("test.txt", test_content, "text/plain")
        }
        
        self.client.post("/api/v1/files/upload", 
                        files=files, 
                        headers=self.headers)
    
    @task(1)
    def get_usage_stats(self):
        """Get usage statistics."""
        self.client.get("/api/v1/usage/stats", headers=self.headers)
    
    @task(1)
    def health_check(self):
        """Check application health."""
        self.client.get("/health")


class ContentGenerationUser(HttpUser):
    """Simulate heavy content generation workload."""
    
    wait_time = between(5, 10)
    
    def on_start(self):
        """Called when a user starts."""
        self.login()
    
    def login(self):
        """Login as a test user."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(10)
    def generate_large_content(self):
        """Generate large content articles."""
        content_data = {
            "title": f"Large Test Article {random.randint(1, 1000)}",
            "brief": "This is a test brief for large content generation performance testing. " * 10,
            "target_words": random.randint(2000, 5000),
            "style_profile_id": "1"
        }
        
        self.client.post("/api/v1/content/generate", 
                        json=content_data, 
                        headers=self.headers)
    
    @task(5)
    def analyze_style(self):
        """Analyze style from reference articles."""
        self.client.post("/api/v1/styles/1/analyze", 
                        headers=self.headers)
    
    @task(3)
    def get_content_status(self):
        """Check content generation status."""
        self.client.get("/api/v1/content/", headers=self.headers)


class APIStressUser(HttpUser):
    """Simulate API stress testing."""
    
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Called when a user starts."""
        self.login()
    
    def login(self):
        """Login as a test user."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(20)
    def rapid_api_calls(self):
        """Make rapid API calls."""
        endpoints = [
            "/api/v1/users/me",
            "/api/v1/organizations/",
            "/api/v1/styles/",
            "/api/v1/content/",
            "/api/v1/usage/stats",
            "/health"
        ]
        
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, headers=self.headers)
    
    @task(10)
    def concurrent_requests(self):
        """Make concurrent requests."""
        import threading
        
        def make_request():
            self.client.get("/api/v1/users/me", headers=self.headers)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()


class DatabaseStressUser(HttpUser):
    """Simulate database stress testing."""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Called when a user starts."""
        self.login()
    
    def login(self):
        """Login as a test user."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(5)
    def create_and_delete_style(self):
        """Create and immediately delete a style profile."""
        # Create style
        style_data = {
            "name": f"Temp Style {random.randint(1, 10000)}",
            "description": "Temporary style for stress testing",
            "tone": "professional",
            "voice": "authoritative",
            "target_audience": "general",
            "content_type": "article"
        }
        
        response = self.client.post("/api/v1/styles/", 
                                  json=style_data, 
                                  headers=self.headers)
        
        if response.status_code == 201:
            style_id = response.json()["id"]
            # Delete style
            self.client.delete(f"/api/v1/styles/{style_id}", 
                             headers=self.headers)
    
    @task(3)
    def bulk_content_operations(self):
        """Perform bulk content operations."""
        # Create multiple content items
        for i in range(5):
            content_data = {
                "title": f"Bulk Content {random.randint(1, 10000)}",
                "brief": f"Bulk content brief {i}",
                "target_words": 1000,
                "style_profile_id": "1"
            }
            
            self.client.post("/api/v1/content/generate", 
                           json=content_data, 
                           headers=self.headers)
    
    @task(2)
    def complex_queries(self):
        """Execute complex database queries."""
        # Get content with filters
        self.client.get("/api/v1/content/?status=completed&limit=100", 
                       headers=self.headers)
        
        # Get usage history
        self.client.get("/api/v1/usage/history?limit=1000", 
                       headers=self.headers)


# Performance benchmarks
class PerformanceBenchmarks:
    """Define performance benchmarks and thresholds."""
    
    # Response time thresholds (in milliseconds)
    RESPONSE_TIME_THRESHOLDS = {
        "health_check": 100,
        "user_profile": 200,
        "content_list": 500,
        "style_list": 300,
        "content_generation": 5000,
        "file_upload": 2000,
        "style_analysis": 3000
    }
    
    # Throughput thresholds (requests per second)
    THROUGHPUT_THRESHOLDS = {
        "api_calls": 100,
        "content_generation": 10,
        "file_uploads": 20
    }
    
    # Error rate thresholds (percentage)
    ERROR_RATE_THRESHOLDS = {
        "max_error_rate": 1.0
    }
    
    @classmethod
    def validate_performance(cls, stats):
        """Validate performance against benchmarks."""
        results = {
            "passed": True,
            "violations": []
        }
        
        # Check response times
        for endpoint, threshold in cls.RESPONSE_TIME_THRESHOLDS.items():
            if endpoint in stats:
                avg_response_time = stats[endpoint]["avg_response_time"]
                if avg_response_time > threshold:
                    results["passed"] = False
                    results["violations"].append({
                        "metric": "response_time",
                        "endpoint": endpoint,
                        "threshold": threshold,
                        "actual": avg_response_time
                    })
        
        # Check throughput
        for operation, threshold in cls.THROUGHPUT_THRESHOLDS.items():
            if operation in stats:
                throughput = stats[operation]["throughput"]
                if throughput < threshold:
                    results["passed"] = False
                    results["violations"].append({
                        "metric": "throughput",
                        "operation": operation,
                        "threshold": threshold,
                        "actual": throughput
                    })
        
        # Check error rate
        total_requests = sum(stats.get("total_requests", {}).values())
        total_errors = sum(stats.get("total_errors", {}).values())
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        if error_rate > cls.ERROR_RATE_THRESHOLDS["max_error_rate"]:
            results["passed"] = False
            results["violations"].append({
                "metric": "error_rate",
                "threshold": cls.ERROR_RATE_THRESHOLDS["max_error_rate"],
                "actual": error_rate
            })
        
        return results


# Load testing scenarios
class LoadTestScenarios:
    """Define different load testing scenarios."""
    
    @staticmethod
    def light_load():
        """Light load scenario - normal usage."""
        return {
            "users": 10,
            "spawn_rate": 2,
            "duration": "5m"
        }
    
    @staticmethod
    def medium_load():
        """Medium load scenario - moderate usage."""
        return {
            "users": 50,
            "spawn_rate": 5,
            "duration": "10m"
        }
    
    @staticmethod
    def heavy_load():
        """Heavy load scenario - high usage."""
        return {
            "users": 100,
            "spawn_rate": 10,
            "duration": "15m"
        }
    
    @staticmethod
    def stress_test():
        """Stress test scenario - beyond normal capacity."""
        return {
            "users": 200,
            "spawn_rate": 20,
            "duration": "20m"
        }
    
    @staticmethod
    def spike_test():
        """Spike test scenario - sudden traffic increase."""
        return {
            "users": 500,
            "spawn_rate": 50,
            "duration": "5m"
        }


# Performance monitoring
class PerformanceMonitor:
    """Monitor performance during load testing."""
    
    def __init__(self):
        self.metrics = {}
    
    def record_metric(self, name, value, timestamp=None):
        """Record a performance metric."""
        if timestamp is None:
            timestamp = time.time()
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            "value": value,
            "timestamp": timestamp
        })
    
    def get_average(self, name):
        """Get average value for a metric."""
        if name not in self.metrics:
            return 0
        
        values = [m["value"] for m in self.metrics[name]]
        return sum(values) / len(values) if values else 0
    
    def get_percentile(self, name, percentile):
        """Get percentile value for a metric."""
        if name not in self.metrics:
            return 0
        
        values = sorted([m["value"] for m in self.metrics[name]])
        index = int(len(values) * percentile / 100)
        return values[index] if values else 0
    
    def generate_report(self):
        """Generate performance report."""
        report = {
            "summary": {},
            "metrics": {}
        }
        
        for name, data in self.metrics.items():
            values = [m["value"] for m in data]
            report["metrics"][name] = {
                "count": len(values),
                "average": sum(values) / len(values) if values else 0,
                "min": min(values) if values else 0,
                "max": max(values) if values else 0,
                "p50": self.get_percentile(name, 50),
                "p95": self.get_percentile(name, 95),
                "p99": self.get_percentile(name, 99)
            }
        
        return report
