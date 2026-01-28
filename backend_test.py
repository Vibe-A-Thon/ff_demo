#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class FraudForgeAPITester:
    def __init__(self, base_url="https://fightfraud-app.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    "name": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "name": name,
                "error": str(e)
            })
            return False, {}

    def test_health_check(self):
        """Test basic health endpoint"""
        return self.run_test("Health Check", "GET", "api/health", 200)

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root Endpoint", "GET", "api/", 200)

    def test_seed_data(self):
        """Test seeding demo data"""
        success, response = self.run_test("Seed Demo Data", "POST", "api/seed-data", 200)
        if success:
            print(f"   Seeded: {response.get('rules', 0)} rules, {response.get('nodes', 0)} nodes, {response.get('battles', 0)} battles")
        return success, response

    def test_battles_api(self):
        """Test battle-related endpoints"""
        print("\n📊 Testing Battle APIs...")
        
        # Get all battles
        success, battles = self.run_test("Get All Battles", "GET", "api/battles", 200)
        if not success:
            return False
        
        if battles:
            battle_id = battles[0]['id']
            
            # Get specific battle
            self.run_test("Get Specific Battle", "GET", f"api/battles/{battle_id}", 200)
            
            # Start battle
            self.run_test("Start Battle", "POST", f"api/battles/{battle_id}/start", 200)
            
            # Stop battle
            self.run_test("Stop Battle", "POST", f"api/battles/{battle_id}/stop", 200)
        
        # Create new battle
        battle_data = {
            "scenario_name": "Test Battle API",
            "parameters": {"difficulty": "medium", "max_turns": 10}
        }
        success, new_battle = self.run_test("Create Battle", "POST", "api/battles", 200, battle_data)
        
        if success and new_battle:
            # Delete the test battle
            self.run_test("Delete Battle", "DELETE", f"api/battles/{new_battle['id']}", 200)
        
        return True

    def test_rules_api(self):
        """Test rule-related endpoints"""
        print("\n🛡️ Testing Rules APIs...")
        
        # Get all rules
        success, rules = self.run_test("Get All Rules", "GET", "api/rules", 200)
        if not success:
            return False
        
        # Create new rule
        rule_data = {
            "name": "TEST-001",
            "description": "Test rule for API testing",
            "rule_type": "velocity",
            "conditions": [{"field": "tx_count", "operator": ">", "value": 5}],
            "actions": [{"type": "flag", "severity": "medium"}],
            "priority": 1
        }
        success, new_rule = self.run_test("Create Rule", "POST", "api/rules", 200, rule_data)
        
        if success and new_rule:
            rule_id = new_rule['id']
            
            # Get specific rule
            self.run_test("Get Specific Rule", "GET", f"api/rules/{rule_id}", 200)
            
            # Update rule
            updated_rule_data = {**rule_data, "description": "Updated test rule"}
            self.run_test("Update Rule", "PUT", f"api/rules/{rule_id}", 200, updated_rule_data)
            
            # Test rule
            self.run_test("Test Rule", "POST", f"api/rules/{rule_id}/test", 200)
            
            # Delete rule
            self.run_test("Delete Rule", "DELETE", f"api/rules/{rule_id}", 200)
        
        return True

    def test_knowledge_nodes_api(self):
        """Test knowledge graph endpoints"""
        print("\n🧠 Testing Knowledge Nodes APIs...")
        
        # Get all nodes
        success, nodes = self.run_test("Get All Knowledge Nodes", "GET", "api/knowledge-nodes", 200)
        if not success:
            return False
        
        # Create new node
        node_data = {
            "node_type": "rule",
            "name": "Test Node",
            "data": {"test": True},
            "connections": []
        }
        success, new_node = self.run_test("Create Knowledge Node", "POST", "api/knowledge-nodes", 200, node_data)
        
        if success and new_node and len(nodes) > 0:
            node_id = new_node['id']
            target_id = nodes[0]['id']
            
            # Connect nodes
            self.run_test("Connect Nodes", "PUT", f"api/knowledge-nodes/{node_id}/connect/{target_id}", 200)
            
            # Delete node
            self.run_test("Delete Knowledge Node", "DELETE", f"api/knowledge-nodes/{node_id}", 200)
        
        return True

    def test_rsb_packages_api(self):
        """Test RSB package endpoints"""
        print("\n📦 Testing RSB Packages APIs...")
        
        # Get all packages
        success, packages = self.run_test("Get All RSB Packages", "GET", "api/rsb-packages", 200)
        if not success:
            return False
        
        # Create new package
        package_data = {
            "name": "Test Package",
            "version": "1.0.0",
            "description": "Test RSB package",
            "manifest": {"rules": 1, "patterns": 1},
            "rules": [],
            "compliance_badges": ["TEST"]
        }
        success, new_package = self.run_test("Create RSB Package", "POST", "api/rsb-packages", 200, package_data)
        
        if success and new_package:
            package_id = new_package['id']
            
            # Get specific package
            self.run_test("Get Specific RSB Package", "GET", f"api/rsb-packages/{package_id}", 200)
            
            # Test package
            self.run_test("Test RSB Package", "POST", f"api/rsb-packages/{package_id}/test", 200)
            
            # Merge package
            self.run_test("Merge RSB Package", "POST", f"api/rsb-packages/{package_id}/merge", 200)
            
            # Delete package
            self.run_test("Delete RSB Package", "DELETE", f"api/rsb-packages/{package_id}", 200)
        
        return True

    def test_evidence_packs_api(self):
        """Test evidence pack endpoints"""
        print("\n🔍 Testing Evidence Packs APIs...")
        
        # Get all evidence packs
        success, packs = self.run_test("Get All Evidence Packs", "GET", "api/evidence-packs", 200)
        if not success:
            return False
        
        # Get battles to generate evidence from
        success, battles = self.run_test("Get Battles for Evidence", "GET", "api/battles", 200)
        if success and battles:
            battle_id = battles[0]['id']
            
            # Generate evidence pack
            success, new_pack = self.run_test("Generate Evidence Pack", "POST", f"api/evidence-packs/generate/{battle_id}", 200)
            
            if success and new_pack:
                pack_id = new_pack['id']
                
                # Get specific evidence pack
                self.run_test("Get Specific Evidence Pack", "GET", f"api/evidence-packs/{pack_id}", 200)
                
                # Export evidence pack
                self.run_test("Export Evidence Pack", "GET", f"api/evidence-packs/{pack_id}/export", 200)
        
        return True

    def test_approvals_api(self):
        """Test approval endpoints"""
        print("\n✅ Testing Approvals APIs...")
        
        # Get all approvals
        success, approvals = self.run_test("Get All Approvals", "GET", "api/approvals", 200)
        if not success:
            return False
        
        # Create new approval
        approval_data = {
            "resource_type": "rule",
            "resource_id": "test-resource-id",
            "action": "deploy",
            "requestor_id": "test-user"
        }
        success, new_approval = self.run_test("Create Approval", "POST", "api/approvals", 200, approval_data)
        
        if success and new_approval:
            approval_id = new_approval['id']
            
            # Approve request
            self.run_test("Approve Request", "POST", f"api/approvals/{approval_id}/approve?approver_id=admin", 200)
        
        return True

    def test_metrics_api(self):
        """Test metrics dashboard endpoint"""
        print("\n📈 Testing Metrics APIs...")
        
        return self.run_test("Get Dashboard Metrics", "GET", "api/metrics/dashboard", 200)[0]

    def test_ai_thinking_api(self):
        """Test AI thinking endpoint"""
        print("\n🤖 Testing AI Thinking APIs...")
        
        thinking_data = {
            "stage": "analysis",
            "context": "Test battle scenario",
            "team": "blue"
        }
        return self.run_test("AI Think", "POST", "api/ai/think", 200, thinking_data)[0]

def main():
    print("🚀 Starting Fraud Forge API Testing...")
    print("=" * 60)
    
    tester = FraudForgeAPITester()
    
    # Test basic connectivity
    if not tester.test_health_check()[0]:
        print("❌ Health check failed - API may be down")
        return 1
    
    if not tester.test_root_endpoint()[0]:
        print("❌ Root endpoint failed")
        return 1
    
    # Seed demo data first
    print("\n🌱 Seeding demo data...")
    tester.test_seed_data()
    
    # Run all API tests
    test_functions = [
        tester.test_battles_api,
        tester.test_rules_api,
        tester.test_knowledge_nodes_api,
        tester.test_rsb_packages_api,
        tester.test_evidence_packs_api,
        tester.test_approvals_api,
        tester.test_metrics_api,
        tester.test_ai_thinking_api,
    ]
    
    for test_func in test_functions:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test function {test_func.__name__} failed with error: {e}")
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.failed_tests:
        print(f"\n❌ Failed Tests ({len(tester.failed_tests)}):")
        for i, failure in enumerate(tester.failed_tests[:5], 1):  # Show first 5 failures
            print(f"   {i}. {failure['name']}")
            if 'error' in failure:
                print(f"      Error: {failure['error']}")
            else:
                print(f"      Expected: {failure['expected']}, Got: {failure['actual']}")
    
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())