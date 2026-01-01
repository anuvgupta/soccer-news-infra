import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from openai import OpenAI
import boto3


def invoke_browser_lambda(url, operation=None, keyword=None, timeout=60000, delay=5000):
    """
    Invoke the Browser Lambda function to fetch rendered HTML
    
    Args:
        url: The URL to fetch
        operation: Operation to perform (e.g., 'find_classes')
        keyword: Keyword for the operation (e.g., class name to find)
        timeout: Navigation timeout in milliseconds (default: 60000)
        delay: Additional delay after page load in milliseconds (default: 5000)
    
    Returns:
        str: HTML content (full page or extracted based on operation)
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
    
    # Add operation and keyword if provided
    if operation:
        payload['operation'] = operation
    if keyword:
        payload['keyword'] = keyword
    
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

For each completed match, the format is: Team1Name, Team1Score - Team2Score, Team2Name

CRITICAL - Understanding the score format and determining the winner:
- The score format is "X-Y" where X is team1's score and Y is team2's score
- Example: score "1-3" means team1 scored 1 goal, team2 scored 3 goals → team2 wins (higher score)
- Example: score "4-1" means team1 scored 4 goals, team2 scored 1 goal → team1 wins (higher score)
- Example: score "2-2" means team1 scored 2 goals, team2 scored 2 goals → Draw (equal scores)
- The winner is ALWAYS the team with the HIGHER score
- If X > Y, then team1 wins
- If Y > X, then team2 wins  
- If X = Y, then it's a "Draw"

For each completed match (matches that have finished with a final score), extract:
- team1: The first team name
- team2: The second team name
- winner: The team with the higher score (or "Draw" if scores are equal)
- score: The final score in format "X-Y" where X=team1's score, Y=team2's score
- match_url: The ESPN match page URL (format: https://www.espn.com/soccer/match/_/gameId/######)

Return JSON with this exact structure:
{{
  "matches": [
    {{
      "team1": "Arsenal",
      "team2": "Aston Villa",
      "winner": "Arsenal",
      "score": "4-1",
      "match_url": "https://www.espn.com/soccer/match/_/gameId/740776"
    }},
    {{
      "team1": "Nottingham Forest",
      "team2": "Everton",
      "winner": "Everton",
      "score": "0-2",
      "match_url": "https://www.espn.com/soccer/match/_/gameId/740783"
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
        
        # 1. Get previous day's date in PST/PDT (Pacific time)
        pacific_tz = ZoneInfo("America/Los_Angeles")
        now_pacific = datetime.now(pacific_tz)
        yesterday_pacific = now_pacific - timedelta(days=1)
        
        yesterday = yesterday_pacific.strftime('%Y%m%d')
        yesterday_readable = yesterday_pacific.strftime('%B %d, %Y')
        
        print(f"Processing soccer matches for: {yesterday_readable}")
        print("=" * 60)
        
        # 2. Build URL and fetch HTML via Browser Lambda with find_classes operation
        url = f"https://www.espn.com/soccer/schedule/_/date/{yesterday}"
        print(f"\nFetching HTML from: {url}")
        print(f"Operation: find_classes, Keyword: ScheduleTables")
        html = invoke_browser_lambda(
            url=url,
            operation='find_classes',
            keyword='ScheduleTables'
        )
        
        # 3. Debug: Print the HTML we received
        print(f"\nReceived HTML length: {len(html)} characters")
        print("\n" + "=" * 80)
        print("DEBUG: HTML CONTENT FROM BROWSER LAMBDA")
        print("=" * 80)
        print(html)
        print("=" * 80 + "\n")
        
        # Use the HTML directly (no need to truncate since we already extracted specific classes)
        truncated_html = html[:50000]  # Still limit to 50K for GPT token limits
        
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
