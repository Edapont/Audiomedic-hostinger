import requests
import sys
import json
import tempfile
import os
from datetime import datetime

class AudioMedicAPITester:
    def __init__(self, base_url="https://medtranscribe-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if not files:
            headers['Content-Type'] = 'application/json'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, headers={k: v for k, v in headers.items() if k != 'Content-Type'}, 
                                           data=data, files=files, timeout=60)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Response: {error_data}"
                except:
                    details += f", Response: {response.text[:200]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_api_health(self):
        """Test API health endpoint"""
        return self.run_test("API Health Check", "GET", "", 200)

    def test_user_registration(self):
        """Test user registration - should create expired user"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_user = {
            "email": f"test_user_{timestamp}@audiomedic.com",
            "password": "TestPass123!",
            "name": f"Dr. Test User {timestamp}"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user
        )
        
        if success:
            self.user_data = test_user
            # Verify user starts with expired subscription
            if response.get('subscription_status') == 'expired' and response.get('subscription_end_date') is None:
                self.log_test("User Registration - Expired Status Check", True, "User correctly starts with expired subscription")
                return True
            else:
                self.log_test("User Registration - Expired Status Check", False, f"Expected expired status with no end date, got: {response.get('subscription_status')}, {response.get('subscription_end_date')}")
                return False
        return False

    def test_user_login(self):
        """Test user login"""
        if not self.user_data:
            self.log_test("User Login", False, "No user data available")
            return False
            
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            return True
        return False

    def test_get_transcriptions_empty(self):
        """Test getting transcriptions (should be empty initially)"""
        success, response = self.run_test(
            "Get Transcriptions (Empty)",
            "GET",
            "transcriptions",
            200
        )
        
        if success and isinstance(response, list) and len(response) == 0:
            return True
        elif success:
            self.log_test("Get Transcriptions (Empty)", False, f"Expected empty list, got: {len(response)} items")
            return False
        return False

    def test_expired_user_transcription_blocked(self):
        """Test that expired users cannot create transcriptions (should get 403)"""
        # Create a small test audio file (WebM format)
        test_audio_content = b'GkXfo0AgQoaBAUL3gQFC8oEEQvOBCEKCQAR3ZWJtQoeBAkKFgQIYU4BnQI0VSalmQCgq17FAAw9CQE2AQAZ3aGFtbXlXQUAGd2hhbW15RIlACECPQAAAAAAAFlSua0AxrkAu14EBY8WBAZyBACK1nEADdW5khkAFVl9WUDglhohAA1ZQOIOBAeBABrCBCLqBCB9DtnVAIueBAKNAHIEAAIcJ'
        
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            temp_file.write(test_audio_content)
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as audio_file:
                files = {'file': ('test_audio.webm', audio_file, 'audio/webm')}
                data = {'title': 'Test Consultation Audio'}
                
                success, response = self.run_test(
                    "Expired User Transcription Block (403 Expected)",
                    "POST",
                    "transcriptions/upload",
                    403,  # Should be blocked with 403
                    data=data,
                    files=files
                )
                
                return success
        finally:
            os.unlink(temp_file_path)

    def test_get_specific_transcription(self):
        """Test getting a specific transcription"""
        if not hasattr(self, 'transcription_id'):
            self.log_test("Get Specific Transcription", False, "No transcription ID available")
            return False
            
        success, response = self.run_test(
            "Get Specific Transcription",
            "GET",
            f"transcriptions/{self.transcription_id}",
            200
        )
        
        return success and 'id' in response

    def test_structure_notes(self):
        """Test clinical notes structuring with GPT-5"""
        if not hasattr(self, 'transcription_id'):
            self.log_test("Structure Clinical Notes", False, "No transcription ID available")
            return False
            
        structure_data = {
            "transcription_id": self.transcription_id
        }
        
        success, response = self.run_test(
            "Structure Clinical Notes",
            "POST",
            "transcriptions/structure",
            200,
            data=structure_data
        )
        
        return success and 'structured_notes' in response

    def test_get_transcriptions_with_data(self):
        """Test getting transcriptions after creating one"""
        success, response = self.run_test(
            "Get Transcriptions (With Data)",
            "GET",
            "transcriptions",
            200
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            return True
        elif success:
            self.log_test("Get Transcriptions (With Data)", False, f"Expected non-empty list, got: {len(response)} items")
            return False
        return False

    def test_delete_transcription(self):
        """Test deleting a transcription"""
        if not hasattr(self, 'transcription_id'):
            self.log_test("Delete Transcription", False, "No transcription ID available")
            return False
            
        success, response = self.run_test(
            "Delete Transcription",
            "DELETE",
            f"transcriptions/{self.transcription_id}",
            200
        )
        
        return success

    def test_invalid_token_access(self):
        """Test API access with invalid token"""
        original_token = self.token
        self.token = "invalid_token_12345"
        
        success, response = self.run_test(
            "Invalid Token Access",
            "GET",
            "transcriptions",
            401
        )
        
        self.token = original_token
        return success

    def create_admin_user(self):
        """Create an admin user for testing"""
        timestamp = datetime.now().strftime('%H%M%S')
        admin_user = {
            "email": f"admin_user_{timestamp}@audiomedic.com",
            "password": "AdminPass123!",
            "name": f"Dr. Admin User {timestamp}"
        }
        
        success, response = self.run_test(
            "Admin User Registration",
            "POST",
            "auth/register",
            200,
            data=admin_user
        )
        
        if success:
            self.admin_data = admin_user
            return True
        return False

    def login_as_admin(self):
        """Login as admin user"""
        if not hasattr(self, 'admin_data'):
            self.log_test("Admin Login", False, "No admin data available")
            return False
            
        login_data = {
            "email": self.admin_data["email"],
            "password": self.admin_data["password"]
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'token' in response:
            self.admin_token = response['token']
            return True
        return False

    def test_admin_list_users_without_mfa(self):
        """Test admin can list users without MFA"""
        if not hasattr(self, 'admin_token'):
            self.log_test("Admin List Users Without MFA", False, "No admin token available")
            return False
            
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test(
            "Admin List Users Without MFA",
            "GET",
            "admin/users",
            200
        )
        
        self.token = original_token
        return success

    def test_mfa_status_endpoint(self):
        """Test MFA status endpoint"""
        if not hasattr(self, 'admin_token'):
            self.log_test("MFA Status Check", False, "No admin token available")
            return False
            
        original_token = self.token
        self.token = self.admin_token
        
        success, response = self.run_test(
            "MFA Status Check",
            "GET",
            "auth/mfa-status",
            200
        )
        
        if success:
            # Check if response contains expected fields
            expected_fields = ['mfa_enabled', 'mfa_required', 'mfa_mandatory', 'grace_days_remaining']
            missing_fields = [field for field in expected_fields if field not in response]
            if missing_fields:
                self.log_test("MFA Status Fields Check", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("MFA Status Fields Check", True, "All expected fields present")
        
        self.token = original_token
        return success

    def test_mfa_setup_flow(self):
        """Test MFA setup flow"""
        if not hasattr(self, 'admin_token'):
            self.log_test("MFA Setup Flow", False, "No admin token available")
            return False
            
        original_token = self.token
        self.token = self.admin_token
        
        # Test MFA setup
        success, response = self.run_test(
            "MFA Setup",
            "POST",
            "auth/setup-mfa",
            200
        )
        
        if success and 'secret' in response and 'qr_code' in response and 'backup_codes' in response:
            self.mfa_secret = response['secret']
            self.log_test("MFA Setup Response Check", True, "MFA setup returned all required fields")
        else:
            self.log_test("MFA Setup Response Check", False, f"Missing fields in MFA setup response: {response}")
        
        self.token = original_token
        return success

    def test_admin_subscription_renewal_without_mfa(self):
        """Test admin cannot renew subscriptions without MFA (if admin > 7 days old)"""
        if not hasattr(self, 'admin_token') or not self.user_data:
            self.log_test("Admin Subscription Renewal Without MFA", False, "Missing admin token or user data")
            return False
            
        original_token = self.token
        self.token = self.admin_token
        
        # Try to renew subscription for the test user
        renewal_data = {"months": 1}
        
        # This should work for new admins (within 7-day grace period)
        # But we'll test the endpoint functionality
        success, response = self.run_test(
            "Admin Subscription Renewal (Grace Period)",
            "PUT",
            f"admin/users/{self.user_data.get('id', 'test-id')}/subscription",
            200,  # Should work within grace period
            data=renewal_data
        )
        
        self.token = original_token
        return success

    def test_admin_change_admin_status_without_mfa(self):
        """Test admin cannot change admin status without MFA (if admin > 7 days old)"""
        if not hasattr(self, 'admin_token') or not self.user_data:
            self.log_test("Admin Change Status Without MFA", False, "Missing admin token or user data")
            return False
            
        original_token = self.token
        self.token = self.admin_token
        
        # Try to change admin status for the test user
        success, response = self.run_test(
            "Admin Change Status (Grace Period)",
            "PUT",
            f"admin/users/{self.user_data.get('id', 'test-id')}/admin-status",
            200,  # Should work within grace period
        )
        
        self.token = original_token
        return success

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting AudioMedic Backend API Tests")
        print("=" * 50)
        
        # Test sequence based on review request
        tests = [
            # Basic API health
            self.test_api_health,
            
            # Test 1: No Trial Period for New Users
            self.test_user_registration,  # Should create expired user
            self.test_user_login,
            self.test_expired_user_transcription_blocked,  # Should get 403
            
            # Test 2: Admin MFA Requirements
            self.create_admin_user,
            self.login_as_admin,
            self.test_admin_list_users_without_mfa,  # Should work without MFA
            self.test_mfa_status_endpoint,  # Test MFA status fields
            self.test_mfa_setup_flow,  # Test MFA setup
            
            # Test admin operations (within grace period for new admin)
            self.test_admin_subscription_renewal_without_mfa,
            self.test_admin_change_admin_status_without_mfa,
            
            # Other tests
            self.test_get_transcriptions_empty,
            self.test_invalid_token_access
        ]
        
        for test in tests:
            test()
            print()
        
        # Print summary
        print("=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All backend tests passed!")
            return 0
        else:
            print("⚠️  Some backend tests failed!")
            return 1

def main():
    tester = AudioMedicAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())