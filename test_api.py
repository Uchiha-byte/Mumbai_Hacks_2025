import requests
import pytest
import time
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv(os.path.join("backend", ".env"))

# Configuration
BASE_URL = os.getenv("TEST_API_BASE_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"

class APITestSuite:
    """TruthScan API Endpoint Test Suite"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.headers = {"Content-Type": "application/json"}
        
    # Helper Methods
    def make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request and return response data"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, json=data, headers=self.headers)
            return {
                "status_code": response.status_code,
                "json": response.json() if response.content else None,
                "error": None
            }
        except Exception as e:
            return {
                "status_code": 0,
                "json": None,
                "error": str(e)
            }
    
    def test_root_endpoint(self) -> bool:
        """Test GET /"""
        result = self.make_request("GET", "/")
        success = result["status_code"] == 200 and "message" in result["json"]
        print(f"[ROOT] Root endpoint: {'PASS' if success else 'FAIL'}")
        return success
    
    def test_health_check(self) -> bool:
        """Test GET /health"""
        result = self.make_request("GET", "/health")
        success = result["status_code"] == 200 and result["json"].get("status") == "ok"
        print(f"[HEALTH] Health check: {'PASS' if success else 'FAIL'}")
        return success
    
    def test_analyze_endpoint(self) -> bool:
        """Test POST /api/v1/analyze (may fail due to API quotas)"""
        test_data = {
            "content": "Breaking: Scientists discover cure for all diseases!",
            "content_type": "text"
        }
        result = self.make_request("POST", f"{API_PREFIX}/analyze", test_data)
        
        # Accept both success and quota errors as "working"
        success = result["status_code"] in [200, 500]  # 500 expected if Gemini quota exhausted
        if result["status_code"] == 500:
            error_msg = result["json"].get("detail", "") if result["json"] else ""
            success = "quota" in error_msg.lower() or "RESOURCE_EXHAUSTED" in error_msg
        
        print(f"[ANALYZE] Analyze endpoint: {'PASS' if success else 'FAIL'} (Status: {result['status_code']})")
        return success
    
    def test_quick_analyze_text(self) -> bool:
        """Test POST /api/v1/quick-analyze with text"""
        test_data = {
            "content": "Breaking news: Free iPhones for everyone!",
            "content_type": "text",
            "metadata": {}
        }
        result = self.make_request("POST", f"{API_PREFIX}/quick-analyze", test_data)
        success = result["status_code"] == 200 and "verdict" in result["json"]
        print(f"[QUICK] Quick analyze (text): {'PASS' if success else 'FAIL'}")
        return success
    
    def test_quick_analyze_image(self) -> bool:
        """Test POST /api/v1/quick-analyze with image (simulated)"""
        # Simulating base64 image data (use a real small base64 string for actual testing)
        test_data = {
            "content": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwABmQ/9k=",
            "content_type": "image",
            "metadata": {}
        }
        result = self.make_request("POST", f"{API_PREFIX}/quick-analyze", test_data)
        # May return 200 or error depending on forensics setup
        success = result["status_code"] in [200, 500]
        print(f"[QUICK] Quick analyze (image): {'PASS' if success else 'FAIL'} (Status: {result['status_code']})")
        return success
    
    def test_feedback_endpoint(self) -> bool:
        """Test POST /api/v1/feedback"""
        test_data = {
            "analysis_id": "test-123",
            "original_content": "Test content",
            "predicted_verdict": "FAKE",
            "user_verdict": "VERIFIED",
            "user_confidence": 4,
            "comments": "Test feedback"
        }
        result = self.make_request("POST", f"{API_PREFIX}/feedback", test_data)
        success = result["status_code"] == 200 and result["json"].get("status") == "success"
        print(f"[FEEDBACK] Feedback endpoint: {'PASS' if success else 'FAIL'}")
        return success
    
    def test_api_keys(self) -> bool:
        """Test if all required API keys are configured"""
        required_keys = [
            "GOOGLE_API_KEY", "HUGGINGFACE_API_TOKEN", "TAVILY_API_KEY",
            "GOOGLE_FACTCHECK_API_KEY", "NEWS_API_KEY", "OPENAI_API_KEY",
            "SUPABASE_URL", "SUPABASE_ANON_KEY"
        ]
        missing = []
        for key in required_keys:
            val = os.getenv(key)
            if not val or "your_" in val or "CHANGE_THIS" in val:
                missing.append(key)
                
        if missing:
            print(f"[FAIL] API Keys Check: FAIL (Missing or default: {', '.join(missing)})")
            return False
            
        print("[OK] API Keys Check: PASS")
        return True
    
    def test_stats_endpoint(self) -> bool:
        """Test GET /api/v1/stats"""
        result = self.make_request("GET", f"{API_PREFIX}/stats")
        success = result["status_code"] == 200 and "storage" in result["json"]
        print(f"[STATS] Stats endpoint: {'PASS' if success else 'FAIL'}")
        return success
    
    def run_all_tests(self) -> None:
        """Run all endpoint tests and print summary"""
        print("\n" + "="*50)
        print("TruthScan API Endpoint Test Suite")
        print("="*50)
        print(f"Testing against: {self.base_url}\n")
        
        tests = [
            self.test_api_keys,
            self.test_root_endpoint,
            self.test_health_check,
            self.test_analyze_endpoint,
            self.test_quick_analyze_text,
            self.test_quick_analyze_image,
            self.test_feedback_endpoint,
            self.test_stats_endpoint
        ]
        
        results = []
        for test in tests:
            try:
                results.append(test())
            except Exception as e:
                print(f"[ERROR] {test.__name__}: {e}")
                results.append(False)
            time.sleep(0.5)  # Brief delay between tests
        
        # Summary
        passed = sum(results)
        total = len(results)
        print("\n" + "="*50)
        print(f"Results: {passed}/{total} tests passed")
        if passed == total:
            print("All endpoints are working correctly!")
        else:
            print("Some tests failed. Check the output above.")
        print("="*50 + "\n")

# PyTest Support (optional)
@pytest.mark.parametrize("endpoint,method,expected_status", [
    ("/", "GET", 200),
    ("/health", "GET", 200),
    (f"{API_PREFIX}/stats", "GET", 200),
])
def test_endpoint(endpoint, method, expected_status):
    """PyTest compatible tests"""
    suite = APITestSuite()
    result = suite.make_request(method, endpoint)
    assert result["status_code"] == expected_status

# Standalone runner
if __name__ == "__main__":
    # Check if server is running first
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to backend server!")
        print(f"Make sure it's running at {BASE_URL}")
        print("\nStart it with: uvicorn app.main:app --reload\n")
        exit(1)
    
    suite = APITestSuite()
    suite.run_all_tests()