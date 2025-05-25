#!/usr/bin/env python3

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/config.env')

def test_progressive_queries():
    api_key = os.getenv('CYANITE_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Very basic advancedSearch
    print("🧪 Test 1: Basic advancedSearch structure")
    query1 = """
    query($searchText: String!) {
      advancedSearch(text: $searchText, first: 1) {
        __typename
      }
    }
    """
    
    test_query(headers, query1, {"searchText": "Ed Sheeran"}, "Test 1")
    
    # Test 2: advancedSearch with connection structure
    print("\n🧪 Test 2: advancedSearch with connection")
    query2 = """
    query($searchText: String!) {
      advancedSearch(text: $searchText, first: 1) {
        ... on AdvancedSearchConnection {
          edges {
            node {
              __typename
            }
          }
        }
      }
    }
    """
    
    test_query(headers, query2, {"searchText": "Ed Sheeran"}, "Test 2")
    
    # Test 3: With target specification
    print("\n🧪 Test 3: With spotify target")
    query3 = """
    query($searchText: String!) {
      advancedSearch(text: $searchText, target: { spotify: {} }, first: 1) {
        ... on AdvancedSearchConnection {
          edges {
            node {
              __typename
            }
          }
        }
      }
    }
    """
    
    test_query(headers, query3, {"searchText": "Ed Sheeran"}, "Test 3")

def test_query(headers, query, variables, test_name):
    try:
        response = requests.post(
            "https://api.cyanite.ai/graphql",
            headers=headers,
            json={"query": query, "variables": variables},
            timeout=30
        )
        
        print(f"{test_name} - Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Error: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_progressive_queries() 