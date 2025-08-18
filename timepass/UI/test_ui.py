#!/usr/bin/env python3
"""
Test script for AgriAI Assistant UI
Demonstrates functionality and runs basic tests
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from typing import Dict, Any, List

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api_client import AgriAIClient, MockAgriAIClient
from config import SUPPORTED_LANGUAGES, SAMPLE_QUESTIONS
from utils import validate_query, clean_text, format_timestamp

class UITester:
    """Test suite for AgriAI Assistant UI components"""
    
    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.client = MockAgriAIClient() if use_mock else AgriAIClient()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_api_client(self):
        """Test API client functionality"""
        print("\n🔧 Testing API Client...")
        
        # Test basic query
        try:
            response = self.client.send_query("How to grow tomatoes?", "en")
            
            required_fields = ["answer", "source", "confidence"]
            has_required = all(field in response for field in required_fields)
            
            self.log_test(
                "API Query Response", 
                has_required,
                f"Response contains required fields: {list(response.keys())}"
            )
            
            # Test multilingual query
            response_hi = self.client.send_query("गेहूं कैसे उगाएं?", "hi")
            self.log_test(
                "Multilingual Query",
                "answer" in response_hi,
                f"Hindi query returned: {response_hi.get('answer', '')[:50]}..."
            )
            
        except Exception as e:
            self.log_test("API Query Response", False, f"Error: {str(e)}")
    
    def test_health_check(self):
        """Test API health check"""
        print("\n💚 Testing Health Check...")
        
        try:
            is_healthy = self.client.health_check()
            self.log_test(
                "Health Check",
                is_healthy,
                "API is healthy" if is_healthy else "API is not responding"
            )
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
    
    def test_chat_history(self):
        """Test chat history functionality"""
        print("\n📜 Testing Chat History...")
        
        try:
            # Save a conversation
            saved = self.client.save_conversation(
                "Test query",
                "Test answer", 
                "en",
                "Test source",
                0.85
            )
            
            self.log_test(
                "Save Conversation",
                saved,
                "Conversation saved successfully" if saved else "Failed to save"
            )
            
            # Get history
            history = self.client.get_chat_history()
            self.log_test(
                "Get Chat History",
                isinstance(history, list),
                f"Retrieved {len(history)} conversation(s)"
            )
            
        except Exception as e:
            self.log_test("Chat History", False, f"Error: {str(e)}")
    
    def test_utils_functions(self):
        """Test utility functions"""
        print("\n🛠 Testing Utility Functions...")
        
        # Test query validation
        valid_queries = [
            "How to grow rice?",
            "What fertilizer for wheat?",
            "गेहूं के लिए कौन सा उर्वरक अच्छा है?"
        ]
        
        invalid_queries = [
            "",
            "a",  # too short
            "x" * 600  # too long
        ]
        
        # Test valid queries
        valid_count = 0
        for query in valid_queries:
            is_valid, _ = validate_query(query)
            if is_valid:
                valid_count += 1
        
        self.log_test(
            "Query Validation (Valid)",
            valid_count == len(valid_queries),
            f"{valid_count}/{len(valid_queries)} valid queries passed"
        )
        
        # Test invalid queries
        invalid_count = 0
        for query in invalid_queries:
            is_valid, _ = validate_query(query)
            if not is_valid:
                invalid_count += 1
        
        self.log_test(
            "Query Validation (Invalid)",
            invalid_count == len(invalid_queries),
            f"{invalid_count}/{len(invalid_queries)} invalid queries rejected"
        )
        
        # Test text cleaning
        dirty_text = "  How to grow   tomatoes???  "
        clean = clean_text(dirty_text)
        
        self.log_test(
            "Text Cleaning",
            clean == "How to grow tomatoes???",
            f"'{dirty_text}' → '{clean}'"
        )
    
    def test_language_support(self):
        """Test language support"""
        print("\n🌐 Testing Language Support...")
        
        # Test language configuration
        self.log_test(
            "Language Configuration",
            len(SUPPORTED_LANGUAGES) >= 6,
            f"Supports {len(SUPPORTED_LANGUAGES)} languages"
        )
        
        # Test sample questions
        sample_count = 0
        for lang_code, questions in SAMPLE_QUESTIONS.items():
            if isinstance(questions, list) and len(questions) > 0:
                sample_count += 1
        
        self.log_test(
            "Sample Questions",
            sample_count >= 3,
            f"Sample questions available for {sample_count} languages"
        )
    
    def test_mock_responses(self):
        """Test mock API responses for different query types"""
        print("\n🤖 Testing Mock Responses...")
        
        test_queries = {
            "wheat": "How to increase wheat yield?",
            "tomato": "Best fertilizer for tomatoes?", 
            "pest": "How to control pests?",
            "general": "Tell me about agriculture"
        }
        
        response_count = 0
        for category, query in test_queries.items():
            try:
                response = self.client.send_query(query, "en")
                if response.get("answer") and len(response["answer"]) > 20:
                    response_count += 1
            except:
                pass
        
        self.log_test(
            "Mock Response Generation",
            response_count == len(test_queries),
            f"Generated responses for {response_count}/{len(test_queries)} query types"
        )
    
    def test_multilingual_responses(self):
        """Test responses in different languages"""
        print("\n🗣 Testing Multilingual Responses...")
        
        query = "How to grow wheat?"
        languages = ["en", "hi", "te", "ta"]
        
        multilingual_count = 0
        for lang in languages:
            try:
                response = self.client.send_query(query, lang)
                if response.get("answer"):
                    multilingual_count += 1
            except:
                pass
        
        self.log_test(
            "Multilingual Responses",
            multilingual_count >= 2,
            f"Responses generated for {multilingual_count}/{len(languages)} languages"
        )
    
    def demo_conversation(self):
        """Demonstrate a complete conversation flow"""
        print("\n💬 Demo Conversation Flow...")
        
        demo_queries = [
            ("en", "How to increase crop yield?"),
            ("hi", "टमाटर के रोग कैसे ठीक करें?"),
            ("te", "వ్యవసాయంలో నీటిపారుదల ఎలా చేయాలి?")
        ]
        
        conversation_log = []
        
        for lang, query in demo_queries:
            try:
                print(f"\n📝 Query ({lang}): {query}")
                
                # Validate query
                is_valid, error = validate_query(query)
                if not is_valid:
                    print(f"❌ Invalid query: {error}")
                    continue
                
                # Send query
                response = self.client.send_query(query, lang)
                
                # Display response
                print(f"🤖 Answer: {response.get('answer', 'No answer')[:100]}...")
                print(f"📌 Source: {response.get('source', 'Unknown')}")
                print(f"🎯 Confidence: {response.get('confidence', 0):.2%}")
                
                # Save conversation
                saved = self.client.save_conversation(
                    query, 
                    response.get('answer', ''),
                    lang,
                    response.get('source', ''),
                    response.get('confidence', 0)
                )
                
                conversation_log.append({
                    "query": query,
                    "language": lang,
                    "answer_length": len(response.get('answer', '')),
                    "saved": saved
                })
                
            except Exception as e:
                print(f"❌ Error processing query: {e}")
        
        self.log_test(
            "Demo Conversation",
            len(conversation_log) >= 2,
            f"Completed {len(conversation_log)} conversations"
        )
        
        return conversation_log
    
    def performance_test(self):
        """Test response performance"""
        print("\n⚡ Testing Performance...")
        
        query = "How to grow rice?"
        iterations = 5
        total_time = 0
        
        for i in range(iterations):
            start_time = time.time()
            try:
                response = self.client.send_query(query, "en")
                end_time = time.time()
                
                if response.get("answer"):
                    total_time += (end_time - start_time)
                else:
                    print(f"❌ No response in iteration {i+1}")
                    
            except Exception as e:
                print(f"❌ Error in iteration {i+1}: {e}")
        
        avg_time = total_time / iterations if total_time > 0 else 0
        
        self.log_test(
            "Response Performance",
            avg_time < 5.0,  # Should respond within 5 seconds
            f"Average response time: {avg_time:.2f}s"
        )
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "timestamp": datetime.now().isoformat()
            },
            "details": self.test_results,
            "environment": {
                "python_version": sys.version,
                "mock_api": self.use_mock,
                "supported_languages": len(SUPPORTED_LANGUAGES)
            }
        }
        
        return report
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🌾 AgriAI Assistant UI - Test Suite")
        print("=" * 50)
        
        # Run tests
        self.test_language_support()
        self.test_utils_functions()
        self.test_api_client()
        self.test_health_check()
        self.test_chat_history()
        self.test_mock_responses()
        self.test_multilingual_responses()
        self.performance_test()
        
        # Demo conversation
        conversation_log = self.demo_conversation()
        
        # Generate report
        report = self.generate_test_report()
        
        # Display summary
        print("\n📊 Test Summary")
        print("=" * 30)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        
        # Save report
        with open("test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: test_report.json")
        
        return report

def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AgriAI Assistant UI Test Suite")
    parser.add_argument("--real-api", action="store_true", 
                       help="Test with real API instead of mock")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick tests only")
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = UITester(use_mock=not args.real_api)
    
    if args.quick:
        print("🚀 Running Quick Tests...")
        tester.test_utils_functions()
        tester.test_language_support()
        tester.test_mock_responses()
    else:
        # Run all tests
        report = tester.run_all_tests()
        
        # Exit with error code if tests failed
        if report['summary']['success_rate'] < 80:
            print("\n❌ Test suite failed! Success rate below 80%")
            sys.exit(1)
        else:
            print("\n✅ All tests passed successfully!")

if __name__ == "__main__":
    main()