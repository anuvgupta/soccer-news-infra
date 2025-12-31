import json
import os
from datetime import datetime, timedelta
from openai import OpenAI
import boto3


def get_date_info():
    """Get current and previous date information for ESPN URLs"""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    return {
        'current_date': today.strftime('%Y%m%d'),
        'previous_date': yesterday.strftime('%Y%m%d'),
        'current_date_readable': today.strftime('%B %d, %Y'),
        'previous_date_readable': yesterday.strftime('%B %d, %Y')
    }


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


def capture_espn_schedule_html(date_string):
    """
    Use Browser Lambda to navigate to ESPN schedule page and capture rendered HTML
    
    Args:
        date_string: Date in YYYYMMDD format (e.g., '20251229')
    
    Returns:
        str: Full HTML content of the rendered page
    """
    espn_url = f"https://www.espn.com/soccer/schedule/_/date/{date_string}"
    
    print(f"Fetching HTML from {espn_url} via Browser Lambda...")
    
    try:
        # Invoke Browser Lambda to fetch the HTML
        html_content = invoke_browser_lambda(
            url=espn_url,
            timeout=60000,  # 60 second timeout
            delay=5000      # 5 second delay after page load
        )
        
        print(f"Successfully captured HTML ({len(html_content)} characters)")
        
        return html_content
        
    except Exception as e:
        print(f"Error in capture_espn_schedule_html: {e}")
        raise


def parse_matches_from_html(client, html_content, date_readable):
    """
    Use GPT-4o to parse the ESPN schedule HTML and extract match data
    
    Args:
        client: OpenAI client instance
        html_content: Full HTML from ESPN schedule page
        date_readable: Human-readable date string
    
    Returns:
        dict: Parsed match data with teams, scores, and URLs
    """
    prompt = f"""You are analyzing an ESPN soccer schedule page for {date_readable}.

I'm providing you with the full HTML content of the page. Please extract all COMPLETED matches (matches that have finished and show a final score).

For each completed match, extract:
1. Team names (home and away)
2. Final score
3. League/Competition name
4. Match URL (should be in format: https://www.espn.com/soccer/match/_/gameId/######)

Return the data as a JSON array with this structure:
{{
  "matches": [
    {{
      "home_team": "Team Name",
      "away_team": "Team Name",
      "home_score": 3,
      "away_score": 1,
      "competition": "English Premier League",
      "match_url": "https://www.espn.com/soccer/match/_/gameId/######"
    }}
  ]
}}

Here is the HTML content:

{html_content[:50000]}

Note: The HTML has been truncated to the first 50,000 characters to fit token limits. Focus on extracting match data from the available content.
"""

    print(f"Sending HTML to GPT-4o for parsing...")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        response_format={"type": "json_object"},
        max_tokens=2000
    )
    
    # Parse the JSON response
    result = json.loads(response.choices[0].message.content)
    
    print(f"GPT-4o successfully parsed {len(result.get('matches', []))} matches")
    
    return result


def format_matches_output(matches_data, date_readable):
    """
    Format the parsed match data into a readable output string
    
    Args:
        matches_data: Dictionary with match data from GPT-4o
        date_readable: Human-readable date string
    
    Returns:
        str: Formatted output string
    """
    matches = matches_data.get('matches', [])
    
    if not matches:
        return f"No completed matches found for {date_readable}"
    
    output_lines = [f"COMPLETED MATCHES FOR {date_readable}"]
    output_lines.append("=" * 60)
    output_lines.append("")
    
    for i, match in enumerate(matches, 1):
        home_team = match.get('home_team', 'Unknown')
        away_team = match.get('away_team', 'Unknown')
        home_score = match.get('home_score', '?')
        away_score = match.get('away_score', '?')
        competition = match.get('competition', 'Unknown')
        match_url = match.get('match_url', 'No URL')
        
        output_lines.append(f"{i}. {home_team} {home_score}-{away_score} {away_team}")
        output_lines.append(f"   Competition: {competition}")
        output_lines.append(f"   Match URL: {match_url}")
        output_lines.append("")
    
    return "\n".join(output_lines)


def handler(event, context):
    """
    Lambda handler that:
    1. Stage 1: Use Browser Lambda to capture ESPN schedule page HTML
    2. Stage 2: Use GPT-4o to parse HTML and extract match data
    3. Print results to console/logs
    """
    try:
        # Get OpenAI API key from environment variable
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError('OPENAI_API_KEY environment variable is not set')
        
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        # Get date information
        date_info = get_date_info()
        print(f"Processing results for previous day: {date_info['previous_date_readable']}")
        print(f"{'='*60}\n")
        
        # Stage 1: Capture HTML using Browser Lambda
        print(f"STAGE 1: CAPTURING HTML WITH BROWSER LAMBDA")
        print(f"{'='*60}")
        html_content = capture_espn_schedule_html(date_info['previous_date'])
        print(f"{'='*60}\n")
        
        # Stage 2: Parse HTML using GPT-4o
        print(f"STAGE 2: PARSING HTML WITH GPT-4o")
        print(f"{'='*60}")
        matches_data = parse_matches_from_html(
            client, 
            html_content, 
            date_info['previous_date_readable']
        )
        print(f"{'='*60}\n")
        
        # Format and print results
        output = format_matches_output(matches_data, date_info['previous_date_readable'])
        print(f"\n{output}\n")
        
        # Return success with match count
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Match extraction completed successfully',
                'date': date_info['previous_date_readable'],
                'match_count': len(matches_data.get('matches', []))
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e
