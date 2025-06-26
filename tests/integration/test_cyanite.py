#!/usr/bin/env python3
"""
Simple test for Cyanite.ai API connectivity
Quick way to verify the API is working before full enrichment
"""

import requests
import json
import os

def test_connection():
    """Test Cyanite.ai API connection - returns result dict for Streamlit integration"""
    
    # Get API key from environment
    api_key = os.getenv('CYANITE_API_KEY')
    
    if not api_key:
        return {"success": False, "error": "CYANITE_API_KEY not found in environment variables"}
    
    # Test query - using libraryTracks to test basic auth and connection
    query = """
    query LibraryTracksQuery {
      libraryTracks(first: 1) { # Requesting just 1 to minimize data transfer for a test
        edges {
          node {
            id
            # audioAnalysisV7 { # Example field, can be commented out if not needed for basic test
            #   __typename
            # }
          }
        }
        pageInfo { # Useful to see if there's more data
            hasNextPage
        }
      }
    }
    """
    
    # This query does not require variables
    # variables = {"text": "The Beatles Hey Jude"} 
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"[DEBUG] Cyanite API Key: {api_key[:10]}...") 
    print(f"[DEBUG] Request Headers: {json.dumps(headers, indent=2)}")
    # print(f"[DEBUG] Request Body: {json.dumps({'query': query, 'variables': variables}, indent=2)}") # Variables removed
    print(f"[DEBUG] Request Body: {json.dumps({'query': query}, indent=2)}")


    try:
        response = requests.post(
            "https://api.cyanite.ai/graphql",
            headers=headers,
            # json={"query": query, "variables": variables}, # Variables removed
            json={"query": query},
            timeout=30
        )
        
        print(f"[DEBUG] Response Status Code: {response.status_code}")
        print(f"[DEBUG] Response Headers: {json.dumps(dict(response.headers), indent=2)}")
        print(f"[DEBUG] Response Raw Text: {response.text}")
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = None 
            print("[DEBUG] Response body is not valid JSON.")

        if response.status_code == 200:
            if data and "errors" in data:
                error_message = data["errors"][0]["message"] if data["errors"] else "Unknown GraphQL error"
                print(f"[DEBUG] GraphQL Error: {error_message}")
                return {"success": False, "error": f"GraphQL Error: {error_message}", "data": data}
            elif data and "data" in data and "libraryTracks" in data["data"]:
                # Even an empty libraryTracks is a success for connection testing
                num_tracks = len(data["data"]["libraryTracks"].get("edges", []))
                print(f"[DEBUG] Successfully connected. Found {num_tracks} tracks in library (for test).")
                return {"success": True, "message": f"Connection successful! Found {num_tracks} library tracks (test).", "data": data["data"]}
            else:
                # Should not happen if status is 200 and no GraphQL errors
                print("[DEBUG] Unexpected 200 response structure.")
                return {"success": False, "error": "Unexpected response structure from API.", "data": data}

        else:
            error_info = f"Unexpected status code: {response.status_code}"
            if data and "errors" in data and data["errors"]:
                 error_info += f", Message: {data['errors'][0]['message']}"
            elif response.text:
                 error_info += f", Response: {response.text[:200]}" # Show first 200 chars of response
            print(f"[DEBUG] Connection failed: {error_info}")
            return {"success": False, "error": error_info, "data": data}

    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Request failed: {e}")
        return {"success": False, "error": f"Request failed: {str(e)}"}

def test_cyanite_api():
    print("🧪 SIMPLE CYANITE.AI API TEST")
    print("=" * 40)
    
    # Get API key
    api_key = input("Enter your Cyanite.ai API key: ").strip()
    
    if not api_key:
        print("❌ API key required")
        return
    
    # Set environment variable temporarily for test
    os.environ['CYANITE_API_KEY'] = api_key
    
    # Use the test_connection function
    result = test_connection()
    
    if result["success"]:
        if result.get("track_found"):
            print(f"✅ SUCCESS! Found track:")
            print(f"   🆔 ID: {result.get('track_id', 'N/A')}")
            print(f"   🎵 Title: {result.get('track_title', 'N/A')}")
            print(f"\n✅ Cyanite.ai API is working correctly with the updated schema!")
            print(f"🚀 You can now run the full enrichment script.")
        else:
            print(f"⚠️ API connected but {result.get('message', 'issue occurred')}")
    else:
        print(f"❌ {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_cyanite_api() 