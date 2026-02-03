#!/usr/bin/env python3
"""
Backend API Testing for DIALIBATOU BTP IMMOBILIER
Tests all the main API endpoints for properties and lots management
"""

import requests
import sys
import json
from datetime import datetime

class BackendAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.issues = []

    def log_issue(self, endpoint, issue, severity="MEDIUM"):
        """Log an issue found during testing"""
        self.issues.append({
            "endpoint": endpoint,
            "issue": issue,
            "severity": severity
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                print(f"❌ Unsupported method: {method}")
                return False, {}

            print(f"   Status: {response.status_code}")
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.content else {}
                except json.JSONDecodeError:
                    return success, {"text": response.text}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                self.log_issue(endpoint, f"Expected {expected_status}, got {response.status_code}", "HIGH")
                return False, {}

        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {str(e)}")
            self.log_issue(endpoint, f"Connection error: {str(e)}", "CRITICAL")
            return False, {}
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout Error: {str(e)}")
            self.log_issue(endpoint, f"Timeout error: {str(e)}", "HIGH")
            return False, {}
        except Exception as e:
            print(f"❌ Unexpected Error: {str(e)}")
            self.log_issue(endpoint, f"Unexpected error: {str(e)}", "HIGH")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "/api/health",
            200
        )
        if success and 'status' in response:
            print(f"   Health status: {response.get('status')}")
        return success

    def test_get_properties(self):
        """Test getting all properties"""
        success, response = self.run_test(
            "Get All Properties",
            "GET",
            "/api/properties",
            200
        )
        if success and isinstance(response, list):
            property_count = len(response)
            print(f"   Found {property_count} properties")
            
            # Check if we have the expected 13 properties (as mentioned in requirements)
            if property_count == 13:
                print(f"✅ Property count matches expectation: 13")
            elif property_count == 12:
                print(f"⚠️  Found 12 properties instead of expected 13")
                self.log_issue("/api/properties", "Found 12 properties instead of expected 13", "MEDIUM")
            else:
                print(f"❌ Unexpected property count: {property_count}")
                self.log_issue("/api/properties", f"Unexpected property count: {property_count}", "HIGH")
            
            # Validate property structure
            if response and len(response) > 0:
                prop = response[0]
                required_fields = ['id', 'ti', 'tr', 'pr', 'nb', 'ty', 'su']
                missing_fields = [field for field in required_fields if field not in prop]
                if missing_fields:
                    print(f"❌ Missing required fields in properties: {missing_fields}")
                    self.log_issue("/api/properties", f"Missing required fields: {missing_fields}", "HIGH")
                else:
                    print(f"✅ Property structure validation passed")
            
            return success, response
        elif success:
            print(f"❌ Expected list of properties, got: {type(response)}")
            self.log_issue("/api/properties", f"Invalid response type: {type(response)}", "HIGH")
        
        return success, []

    def test_get_lots(self):
        """Test getting all lots"""
        success, response = self.run_test(
            "Get All Lots",
            "GET", 
            "/api/lots",
            200
        )
        if success and isinstance(response, list):
            lots_count = len(response)
            print(f"   Found {lots_count} lots")
            
            # Validate lot structure
            if response and len(response) > 0:
                lot = response[0]
                required_fields = ['id', 'loc', 'lots', 'dispo', 'su', 'pr', 'st']
                missing_fields = [field for field in required_fields if field not in lot]
                if missing_fields:
                    print(f"❌ Missing required fields in lots: {missing_fields}")
                    self.log_issue("/api/lots", f"Missing required fields: {missing_fields}", "HIGH")
                else:
                    print(f"✅ Lot structure validation passed")
            
            return success, response
        elif success:
            print(f"❌ Expected list of lots, got: {type(response)}")
            self.log_issue("/api/lots", f"Invalid response type: {type(response)}", "HIGH")
        
        return success, []

    def test_create_property(self):
        """Test creating a new property"""
        test_property = {
            "ti": "Test Property for API Testing",
            "de": "This is a test property created for API testing purposes",
            "ty": "Appartement",
            "tr": "Vente",
            "pr": 50000000,
            "nb": "Test Location",
            "su": 100,
            "ro": 3,
            "be": 2,
            "ba": 1,
            "fe": ["Test Feature"],
            "im": [],
            "vd": [],
            "ft": False,
            "vi": 0
        }

        success, response = self.run_test(
            "Create Property",
            "POST",
            "/api/properties",
            200
        )
        if not success:
            # Try with the test property data
            success, response = self.run_test(
                "Create Property with Data",
                "POST",
                "/api/properties",
                200,
                data=test_property
            )
        
        if success and 'id' in response:
            created_id = response['id']
            print(f"   Created property with ID: {created_id}")
            return success, created_id
        elif success:
            print(f"❌ Expected property with ID, got: {response}")
            self.log_issue("/api/properties", "Property creation didn't return ID", "HIGH")
        
        return success, None

    def test_delete_property(self, property_id):
        """Test deleting a property"""
        if not property_id:
            print("⚠️  Skipping delete test - no property ID provided")
            return True
        
        success, response = self.run_test(
            f"Delete Property {property_id}",
            "DELETE",
            f"/api/properties/{property_id}",
            200
        )
        
        if success and 'message' in response:
            print(f"   Delete response: {response['message']}")
        
        return success

    def test_get_single_property(self, properties):
        """Test getting a single property by ID"""
        if not properties or len(properties) == 0:
            print("⚠️  Skipping single property test - no properties available")
            return True
        
        test_id = properties[0]['id']
        success, response = self.run_test(
            f"Get Property {test_id}",
            "GET",
            f"/api/properties/{test_id}",
            200
        )
        
        if success and response.get('id') == test_id:
            print(f"✅ Retrieved correct property: {response.get('ti', 'Unknown Title')}")
        elif success:
            print(f"❌ Retrieved property ID mismatch: expected {test_id}, got {response.get('id')}")
            self.log_issue(f"/api/properties/{test_id}", "Property ID mismatch in response", "HIGH")
        
        return success

    def run_all_tests(self):
        """Run all backend API tests"""
        print(f"🚀 Starting Backend API Testing for DIALIBATOU BTP IMMOBILIER")
        print(f"   Base URL: {self.base_url}")
        print("=" * 60)

        # Test 1: Health Check
        if not self.test_health_check():
            print("❌ Health check failed - API may not be running")
            self.log_issue("/api/health", "Health check failed - service not available", "CRITICAL")
            return self.generate_report()

        # Test 2: Get Properties
        properties_success, properties = self.test_get_properties()
        
        # Test 3: Get Lots  
        lots_success, lots = self.test_get_lots()

        # Test 4: Get Single Property
        if properties:
            self.test_get_single_property(properties)

        # Test 5: Create Property
        create_success, created_id = self.test_create_property()

        # Test 6: Delete Property (cleanup)
        if created_id:
            self.test_delete_property(created_id)

        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 TEST REPORT")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.issues:
            print(f"\n⚠️  ISSUES FOUND ({len(self.issues)}):")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue['endpoint']}: {issue['issue']} [{issue['severity']}]")
        else:
            print("\n✅ No critical issues found!")
        
        print("=" * 60)
        
        # Return success if at least 80% of tests pass and no critical issues
        critical_issues = [i for i in self.issues if i['severity'] == 'CRITICAL']
        return success_rate >= 80 and len(critical_issues) == 0

def main():
    """Main test function"""
    print("🔧 DIALIBATOU BTP IMMOBILIER - Backend API Testing")
    print("Testing against http://localhost:8001")
    
    tester = BackendAPITester("http://localhost:8001")
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())