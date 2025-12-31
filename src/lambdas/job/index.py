import json
import os
from datetime import datetime, timedelta
from openai import OpenAI
import boto3


def invoke_browser_lambda(url, timeout=60000, delay=5000):
    """
    Invoke the Browser Lambda function to fetch rendered HTML
    
    Args:
        url: The URL to fetch
        timeout: Navigation timeout in milliseconds (default: 60000)
        delay: Additional delay after page load in milliseconds (default: 5000)
    
    Returns:
        str: Full HTML content of the rendered page
    """
    browser_lambda_arn = os.environ.get('BROWSER_LAMBDA_ARN')
    if not browser_lambda_arn:
        raise ValueError('BROWSER_LAMBDA_ARN environment variable is not set')
    
    lambda_client = boto3.client('lambda')
    
    payload = {
        'url': url,
        'waitUntil': 'networkidle0',
        'timeout': timeout,
        'delay': delay
    }
    
    print(f"Invoking Browser Lambda for URL: {url}")
    print(f"Payload: {json.dumps(payload)}")
    
    try:
        response = lambda_client.invoke(
            FunctionName=browser_lambda_arn,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Parse the response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"Browser Lambda response status code: {response_payload.get('statusCode')}")
        
        if response_payload.get('statusCode') == 200:
            body = response_payload.get('body', {})
            html = body.get('html', '')
            final_url = body.get('url', url)
            
            print(f"Successfully fetched HTML from {final_url}")
            print(f"HTML length: {len(html)} characters")
            
            return html
        else:
            error_body = response_payload.get('body', {})
            error_msg = error_body.get('error', 'Unknown error')
            raise Exception(f"Browser Lambda returned error: {error_msg}")
            
    except Exception as e:
        print(f"Error invoking Browser Lambda: {e}")
        raise


def extract_schedule_html(html_content, max_chars=50000):
    """
    Find 'Soccer Schedule</h1>' and return the next 50,000 characters
    
    Args:
        html_content: Full HTML from the page
        max_chars: Maximum characters to extract after marker (default: 50000)
    
    Returns:
        str: Truncated HTML content starting after the marker
    """
    marker = "Soccer Schedule</h1>"
    pos = html_content.find(marker)
    
    if pos == -1:
        # Fallback: if marker not found, use beginning
        print(f"Warning: Marker '{marker}' not found, using first {max_chars} characters")
        return html_content[:max_chars]
    
    # Start AFTER the closing tag
    start_pos = pos + len(marker)
    extracted = html_content[start_pos:start_pos + max_chars]
    
    print(f"Found marker at position {pos}")
    print(f"Extracted {len(extracted)} characters starting after marker")
    
    return extracted


def extract_matches_with_gpt(client, html_content, date_str):
    """
    Use GPT-4o to extract match data from HTML
    
    Args:
        client: OpenAI client instance
        html_content: HTML content (already truncated)
        date_str: Date string in YYYYMMDD format
    
    Returns:
        dict: Match data with structure defined in prompt
    """
    prompt = f"""Extract all completed soccer matches from this ESPN schedule HTML for {date_str}.

For each completed match (matches that have finished with a final score), extract:
- home_team: The first team mentioned (home team)
- away_team: The second team mentioned (away team)
- winning_team: Which team won (or "Draw" if tied)
- score: The final score in format "X-Y" (e.g., "3-1")
- match_url: The ESPN match page URL (format: https://www.espn.com/soccer/match/_/gameId/######)

Return JSON with this exact structure:
{{
  "matches": [
    {{
      "home_team": "Team A",
      "away_team": "Team B", 
      "winning_team": "Team A",
      "score": "3-1",
      "match_url": "https://www.espn.com/soccer/match/_/gameId/123456"
    }}
  ]
}}

HTML content:

{html_content}
"""
    
    print(f"Sending {len(html_content)} characters to GPT-4o for parsing...")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        response_format={"type": "json_object"},
        max_tokens=4000
    )
    
    result = json.loads(response.choices[0].message.content)
    
    print(f"GPT-4o extracted {len(result.get('matches', []))} matches")
    
    return result


def handler(event, context):
    """
    Lambda handler - simplified flow:
    1. Get previous day's date
    2. Build ESPN schedule URL and fetch HTML via Browser Lambda
    3. Intelligently truncate HTML to relevant section
    4. Extract match data using GPT-4o
    5. Print JSON results to console
    """
    try:
        # Get OpenAI API key from environment variable
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError('OPENAI_API_KEY environment variable is not set')
        
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        # 1. Get previous day's date
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        yesterday_readable = (datetime.now() - timedelta(days=1)).strftime('%B %d, %Y')
        
        print(f"Processing soccer matches for: {yesterday_readable}")
        print("=" * 60)
        
        # 2. Build URL and fetch HTML via Browser Lambda
        url = f"https://www.espn.com/soccer/schedule/_/date/{yesterday}"
        print(f"\nFetching HTML from: {url}")
        html = invoke_browser_lambda(url)
        
        # 3. Intelligently truncate HTML to relevant section
        print("\nTruncating HTML to relevant section...")
        truncated_html = extract_schedule_html(html)
        
        # 4. Extract match data using GPT-4o
        print("\nExtracting match data with GPT-4o...")
        result = extract_matches_with_gpt(client, truncated_html, yesterday)
        
        # 5. Print JSON results to console
        print("\n" + "=" * 60)
        print("MATCH RESULTS (JSON):")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("=" * 60)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
