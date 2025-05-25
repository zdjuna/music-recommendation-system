#!/usr/bin/env python3
"""Test Cyanite raw API response"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('CYANITE_API_KEY')
if not api_key:
    print("❌ No CYANITE_API_KEY found")
    exit(1)

# Simple query to test what we get back
query = """
query TestSearch {
  freeTextSearch(
    first: 3
    target: { spotify: {} }
    searchText: "The Beatles Hey Jude"
  ) {
    ... on FreeTextSearchError {
      message
      code
    }
    ... on FreeTextSearchConnection {
      edges {
        node {
          id
          title
          __typename
        }
      }
    }
  }
}
"""

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://api.cyanite.ai/graphql",
    headers=headers,
    json={"query": query}
)

print("Status:", response.status_code)
print("\nResponse:")
print(json.dumps(response.json(), indent=2)) 