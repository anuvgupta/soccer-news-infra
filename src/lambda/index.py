import json
import os
from datetime import datetime, timedelta
from openai import OpenAI


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


def extract_previous_day_matches(client, date_info):
    """
    Stage 1a: Get completed match results from previous day (scores only, no URLs yet)
    Returns: List of completed matches with teams and scores
    """
    espn_url = f"https://www.espn.com/soccer/schedule/_/date/{date_info['previous_date']}"
    
    prompt = f"""Look at the ESPN soccer schedule page for {date_info['previous_date_readable']}:
{espn_url}

List all COMPLETED matches (games that have finished and show a final score).

For each completed match, provide ONLY:
- Team names
- Final score
- League/Competition name

Format as a simple list. Do NOT include URLs yet.
Example format:
- Newcastle United 3-1 Burnley FC (EPL)
- Chelsea 2-2 Bournemouth (EPL)
"""

    print(f"Stage 1a: Getting match results from {espn_url}...")
    
    response = client.chat.completions.create(
        model="gpt-4o-search-preview",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        max_tokens=1500
    )
    
    return response.choices[0].message.content


def find_match_urls(client, matches_text, date_info):
    """
    Stage 1b: Find the specific match page URLs for the matches from stage 1a
    """
    espn_url = f"https://www.espn.com/soccer/schedule/_/date/{date_info['previous_date']}"
    
    prompt = f"""Go to this ESPN soccer schedule page:
{espn_url}

I need the match page URLs for these specific matches:

{matches_text}

For each match listed above, find and click on it to get its specific match page URL.
The URL should be in the format: https://www.espn.com/soccer/match/_/gameId/######

Provide the results as:
Match: [Team1 vs Team2]
URL: [the actual URL with gameId]

Do this for each match in the list.
"""

    print(f"Stage 1b: Finding match URLs...")
    
    response = client.chat.completions.create(
        model="gpt-4o-search-preview",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        max_tokens=2000
    )
    
    return response.choices[0].message.content


def handler(event, context):
    """
    Simplified Lambda handler that:
    1. Stage 1a: Get completed match results from previous day (teams & scores)
    2. Stage 1b: Find the specific match URLs for those matches
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
        
        # Stage 1a: Get match results (scores)
        matches_results = extract_previous_day_matches(client, date_info)
        print(f"\n{'='*60}")
        print(f"STAGE 1A: MATCH RESULTS ({date_info['previous_date_readable']})")
        print(f"{'='*60}")
        print(matches_results)
        print(f"{'='*60}\n")
        
        # Stage 1b: Find URLs for those matches
        match_urls = find_match_urls(client, matches_results, date_info)
        print(f"\n{'='*60}")
        print(f"STAGE 1B: MATCH URLS")
        print(f"{'='*60}")
        print(match_urls)
        print(f"{'='*60}\n")
        
        # Return success
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Match extraction completed successfully',
                'date': date_info['previous_date_readable']
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e

