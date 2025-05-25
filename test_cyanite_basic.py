#!/usr/bin/env python3
"""
Basic Cyanite API test to identify the correct query structure
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/config.env')

def test_basic_query():
    """Test with the most basic query possible"""
    
    api_key = os.getenv('CYANITE_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Try a very simple query first
    query = """
    query {
      __schema {
        types {
          name
        }
      }
    }
    """
    
    print("🧪 Testing basic schema query...")
    
    try:
        response = requests.post(
            "https://api.cyanite.ai/graphql",
            headers=headers,
            json={"query": query},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("✅ Basic API connection works!")
            
            # Now try a simple search query
            search_query = """
            query($searchText: String!) {
              advancedSearch(text: $searchText, first: 1) {
                __typename
              }
            }
            """
            
            print("\n🔍 Testing simple advancedSearch...")
            
            response2 = requests.post(
                "https://api.cyanite.ai/graphql",
                headers=headers,
                json={"query": search_query, "variables": {"searchText": "Ed Sheeran"}},
                timeout=30
            )
            
            print(f"Status: {response2.status_code}")
            print(f"Response: {response2.text[:500]}...")
            
        else:
            print(f"❌ API connection failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_basic_query() 