#!/usr/bin/env python3
"""
Simple test for Cyanite.ai API connectivity
Quick way to verify the API is working before full enrichment
"""

import requests
import json

def test_cyanite_api():
    print("🧪 SIMPLE CYANITE.AI API TEST")
    print("=" * 40)
    
    # Get API key
    api_key = input("Enter your Cyanite.ai API key: ").strip()
    
    if not api_key:
        print("❌ API key required")
        return
    
    # Test query - using advanced search with free text
    query = """
    query AdvancedSearchExample($text: String!) {
      advancedSearch(
        text: $text
        target: { spotify: {} }
        first: 1
      ) {
        ... on AdvancedSearchError {
          code
          message
        }
        ... on AdvancedSearchConnection {
          edges {
            node {
              track {
                ... on AdvancedSearchNodeSpotifyTrack {
                  id
                  name
                  artists
                  durationMs
                }
              }
            }
          }
        }
      }
    }
    """
    
    variables = {"text": "The Beatles Hey Jude"}
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"🔍 Testing with: The Beatles - Hey Jude")
    print(f"🌐 Sending request to Cyanite.ai...")
    
    try:
        response = requests.post(
            "https://api.cyanite.ai/graphql",
            headers=headers,
            json={"query": query, "variables": variables},
            timeout=30
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'errors' in data:
                print(f"❌ API errors: {data['errors']}")
                return
            
            search_result = data.get('data', {}).get('advancedSearch', {})
            
            if search_result.get('__typename') == 'AdvancedSearchConnection':
                edges = search_result.get('edges', [])
                if edges:
                    track_data = edges[0]['node']['track']
                    print(f"✅ SUCCESS! Found track:")
                    print(f"   🎵 Track ID: {track_data.get('id', 'N/A')}")
                    print(f"   🎤 Name: {track_data.get('name', 'N/A')}")
                    print(f"   👥 Artists: {track_data.get('artists', 'N/A')}")
                    print(f"   ⏱️ Duration: {track_data.get('durationMs', 'N/A')}ms")
                    
                    print(f"\n✅ Cyanite.ai API is working correctly!")
                    print(f"🚀 You can now run the full enrichment script.")
                else:
                    print(f"❌ No tracks found. This might indicate:")
                    print(f"   • Track not in Cyanite's database")
                    print(f"   • Search query too specific")
                    print(f"   • API endpoint limitations")
            elif search_result.get('__typename') == 'AdvancedSearchError':
                print(f"❌ Search error: {search_result.get('message', 'Unknown error')}")
                print(f"   Error code: {search_result.get('code', 'N/A')}")
            else:
                print(f"❌ Unexpected response structure: {search_result}")
                
        elif response.status_code == 401:
            print(f"❌ Authentication failed - check your API key")
            
        elif response.status_code == 403:
            print(f"❌ Forbidden - your API key may not have the required permissions")
            
        elif response.status_code == 429:
            print(f"❌ Rate limited - please wait and try again")
            
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out - check your internet connection")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_cyanite_api() 