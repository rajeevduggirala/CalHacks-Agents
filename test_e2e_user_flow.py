#!/usr/bin/env python3
"""
End-to-End User Flow Test Script
Tests complete user journey: Registration → Login → Profile Management
"""

import requests
import json
import time
from typing import Dict, Any, Optional

class E2EUserFlowTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token: Optional[str] = None
        self.user_data: Optional[Dict[str, Any]] = None
        
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def print_step(self, step: str, status: str = "info"):
        """Print a formatted step"""
        icons = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}
        print(f"{icons.get(status, 'ℹ️')} {step}")
    
    def print_response(self, response: requests.Response, title: str = "Response"):
        """Print formatted response"""
        print(f"\n═══ {title} ═══")
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response: {response.text}")
    
    def test_server_health(self) -> bool:
        """Test if server is running and healthy"""
        self.print_header("Server Health Check")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            self.print_response(response, "Health Check")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.print_step("Server is healthy and running", "success")
                    return True
                else:
                    self.print_step("Server health check failed", "error")
                    return False
            else:
                self.print_step(f"Server returned status {response.status_code}", "error")
                return False
                
        except requests.exceptions.ConnectionError:
            self.print_step("Cannot connect to server. Is it running?", "error")
            self.print_step("Start server with: python main.py", "info")
            return False
        except Exception as e:
            self.print_step(f"Unexpected error: {e}", "error")
            return False
    
    def test_user_registration(self) -> bool:
        """Test user registration with comprehensive profile data"""
        self.print_header("User Registration Test")
        
        # Generate unique user data
        timestamp = int(time.time())
        self.user_data = {
            "email": f"testuser{timestamp}@example.com",
            "username": f"testuser{timestamp}",
            "password": "SecurePass123!",
            "name": "Test User",
            "daily_calories": 2000.0,
            "dietary_restrictions": ["vegetarian", "gluten-free", "no nuts"],
            "likes": ["indian", "spicy", "savory", "grilled", "mediterranean"],
            "additional_information": "I prefer low-carb meals after 6pm. Love garlic in everything. Hate overly sweet desserts.",
            "macros": {
                "protein": 120.0,
                "carbs": 200.0,
                "fats": 80.0
            }
        }
        
        self.print_step(f"Registering user: {self.user_data['email']}")
        self.print_step(f"Username: {self.user_data['username']}")
        self.print_step(f"Dietary restrictions: {', '.join(self.user_data['dietary_restrictions'])}")
        self.print_step(f"Likes: {', '.join(self.user_data['likes'])}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=self.user_data
            )
            
            self.print_response(response, "Registration Response")
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.print_step("User registration successful", "success")
                self.print_step(f"User ID: {data.get('user_id')}", "info")
                return True
            else:
                self.print_step("User registration failed", "error")
                return False
                
        except Exception as e:
            self.print_step(f"Registration error: {e}", "error")
            return False
    
    def test_user_login(self) -> bool:
        """Test user login and token retrieval"""
        self.print_header("User Login Test")
        
        if not self.user_data:
            self.print_step("No user data available for login", "error")
            return False
        
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        self.print_step(f"Logging in user: {login_data['email']}")
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data
            )
            
            self.print_response(response, "Login Response")
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                
                if self.auth_token:
                    self.print_step("Login successful", "success")
                    self.print_step(f"Token received: {self.auth_token[:20]}...", "info")
                    self.print_step(f"User name: {data.get('user_name')}", "info")
                    return True
                else:
                    self.print_step("No access token in response", "error")
                    return False
            else:
                self.print_step("Login failed", "error")
                return False
                
        except Exception as e:
            self.print_step(f"Login error: {e}", "error")
            return False
    
    def test_user_profile_retrieval(self) -> bool:
        """Test retrieving user profile with authentication"""
        self.print_header("User Profile Retrieval Test")
        
        if not self.auth_token:
            self.print_step("No auth token available", "error")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        self.print_step("Retrieving user profile with authentication")
        
        try:
            response = self.session.get(
                f"{self.base_url}/profile",
                headers=headers
            )
            
            self.print_response(response, "Profile Response")
            
            if response.status_code == 200:
                data = response.json()
                self.print_step("Profile retrieval successful", "success")
                
                # Verify profile data matches registration
                self.print_step("Verifying profile data...", "info")
                
                # Check basic info
                if data.get("email") == self.user_data["email"]:
                    self.print_step("✅ Email matches", "success")
                else:
                    self.print_step("❌ Email mismatch", "error")
                
                if data.get("username") == self.user_data["username"]:
                    self.print_step("✅ Username matches", "success")
                else:
                    self.print_step("❌ Username mismatch", "error")
                
                if data.get("name") == self.user_data["name"]:
                    self.print_step("✅ Name matches", "success")
                else:
                    self.print_step("❌ Name mismatch", "error")
                
                # Check dietary preferences
                profile = data.get("profile", {})
                if profile.get("daily_calories") == self.user_data["daily_calories"]:
                    self.print_step("✅ Daily calories match", "success")
                else:
                    self.print_step("❌ Daily calories mismatch", "error")
                
                if set(profile.get("dietary_restrictions", [])) == set(self.user_data["dietary_restrictions"]):
                    self.print_step("✅ Dietary restrictions match", "success")
                else:
                    self.print_step("❌ Dietary restrictions mismatch", "error")
                
                if set(profile.get("likes", [])) == set(self.user_data["likes"]):
                    self.print_step("✅ Likes match", "success")
                else:
                    self.print_step("❌ Likes mismatch", "error")
                
                if profile.get("additional_information") == self.user_data["additional_information"]:
                    self.print_step("✅ Additional information matches", "success")
                else:
                    self.print_step("❌ Additional information mismatch", "error")
                
                # Check macros
                macros = profile.get("macros", {})
                if macros.get("protein") == self.user_data["macros"]["protein"]:
                    self.print_step("✅ Protein macro matches", "success")
                else:
                    self.print_step("❌ Protein macro mismatch", "error")
                
                return True
            else:
                self.print_step("Profile retrieval failed", "error")
                return False
                
        except Exception as e:
            self.print_step(f"Profile retrieval error: {e}", "error")
            return False
    
    def test_profile_update(self) -> bool:
        """Test updating user profile"""
        self.print_header("User Profile Update Test")
        
        if not self.auth_token:
            self.print_step("No auth token available", "error")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Update profile data
        update_data = {
            "daily_calories": 2200.0,
            "dietary_restrictions": ["vegetarian", "gluten-free", "no nuts", "dairy-free"],
            "likes": ["indian", "spicy", "savory", "grilled", "mediterranean", "thai"],
            "additional_information": "Updated: I prefer low-carb meals after 6pm. Love garlic in everything. Hate overly sweet desserts. Also love fresh herbs.",
            "target_protein_g": 130.0,
            "target_carbs_g": 180.0,
            "target_fat_g": 90.0
        }
        
        self.print_step("Updating user profile with new preferences")
        self.print_step(f"New daily calories: {update_data['daily_calories']}")
        self.print_step(f"New dietary restrictions: {', '.join(update_data['dietary_restrictions'])}")
        self.print_step(f"New likes: {', '.join(update_data['likes'])}")
        
        try:
            response = self.session.put(
                f"{self.base_url}/profile",
                json=update_data,
                headers=headers
            )
            
            self.print_response(response, "Profile Update Response")
            
            if response.status_code == 200:
                data = response.json()
                self.print_step("Profile update successful", "success")
                
                # Verify the update
                self.print_step("Verifying profile update...", "info")
                profile = data.get("profile", {})
                
                if profile.get("daily_calories") == update_data["daily_calories"]:
                    self.print_step("✅ Daily calories updated", "success")
                else:
                    self.print_step("❌ Daily calories not updated", "error")
                
                if set(profile.get("dietary_restrictions", [])) == set(update_data["dietary_restrictions"]):
                    self.print_step("✅ Dietary restrictions updated", "success")
                else:
                    self.print_step("❌ Dietary restrictions not updated", "error")
                
                return True
            else:
                self.print_step("Profile update failed", "error")
                return False
                
        except Exception as e:
            self.print_step(f"Profile update error: {e}", "error")
            return False
    
    def test_unauthorized_access(self) -> bool:
        """Test that protected endpoints require authentication"""
        self.print_header("Unauthorized Access Test")
        
        self.print_step("Testing access to protected endpoint without token")
        
        try:
            response = self.session.get(f"{self.base_url}/profile")
            self.print_response(response, "Unauthorized Access Response")
            
            if response.status_code == 401:
                self.print_step("✅ Unauthorized access properly blocked", "success")
                return True
            else:
                self.print_step("❌ Unauthorized access not blocked", "error")
                return False
                
        except Exception as e:
            self.print_step(f"Unauthorized access test error: {e}", "error")
            return False
    
    def test_user_stats(self) -> bool:
        """Test user statistics endpoint"""
        self.print_header("User Statistics Test")
        
        if not self.auth_token:
            self.print_step("No auth token available", "error")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        self.print_step("Retrieving user statistics")
        
        try:
            response = self.session.get(
                f"{self.base_url}/stats",
                headers=headers
            )
            
            self.print_response(response, "Stats Response")
            
            if response.status_code == 200:
                data = response.json()
                self.print_step("User statistics retrieved successfully", "success")
                self.print_step(f"Total recipes: {data.get('total_recipes', 0)}", "info")
                self.print_step(f"Total grocery lists: {data.get('total_grocery_lists', 0)}", "info")
                self.print_step(f"Total meals logged: {data.get('total_meals_logged', 0)}", "info")
                return True
            else:
                self.print_step("User statistics retrieval failed", "error")
                return False
                
        except Exception as e:
            self.print_step(f"User statistics error: {e}", "error")
            return False
    
    def run_full_test_suite(self) -> Dict[str, bool]:
        """Run the complete end-to-end test suite"""
        print("🚀 Starting End-to-End User Flow Test Suite")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Server Health
        results["server_health"] = self.test_server_health()
        if not results["server_health"]:
            print("\n❌ Server health check failed. Cannot continue tests.")
            return results
        
        # Test 2: User Registration
        results["user_registration"] = self.test_user_registration()
        if not results["user_registration"]:
            print("\n❌ User registration failed. Cannot continue tests.")
            return results
        
        # Test 3: User Login
        results["user_login"] = self.test_user_login()
        if not results["user_login"]:
            print("\n❌ User login failed. Cannot continue tests.")
            return results
        
        # Test 4: Profile Retrieval
        results["profile_retrieval"] = self.test_user_profile_retrieval()
        
        # Test 5: Profile Update
        results["profile_update"] = self.test_profile_update()
        
        # Test 6: Unauthorized Access
        results["unauthorized_access"] = self.test_unauthorized_access()
        
        # Test 7: User Statistics
        results["user_stats"] = self.test_user_stats()
        
        return results
    
    def print_final_summary(self, results: Dict[str, bool]):
        """Print final test summary"""
        self.print_header("Final Test Summary")
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n📋 Detailed Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name.replace('_', ' ').title()}")
        
        if failed_tests == 0:
            print(f"\n🎉 All tests passed! Your user flow is working perfectly!")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed. Check the errors above.")


def main():
    """Main function to run the E2E test suite"""
    print("🧪 Agentic Grocery - End-to-End User Flow Test")
    print("=" * 60)
    print("This script tests the complete user journey:")
    print("1. Server Health Check")
    print("2. User Registration")
    print("3. User Login")
    print("4. Profile Retrieval")
    print("5. Profile Update")
    print("6. Unauthorized Access Protection")
    print("7. User Statistics")
    print("=" * 60)
    
    # Initialize tester
    tester = E2EUserFlowTester()
    
    # Run full test suite
    results = tester.run_full_test_suite()
    
    # Print final summary
    tester.print_final_summary(results)
    
    # Exit with appropriate code
    failed_tests = sum(1 for result in results.values() if not result)
    exit(failed_tests)


if __name__ == "__main__":
    main()
