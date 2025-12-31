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


def extract_current_day_schedule(client, date_info):
    """
    Stage 1a: Use search GPT to extract information from ESPN schedule for current day
    Returns: teams, scores, match URLs for completed games, and teams & times for upcoming games
    """
    espn_url = f"https://www.espn.com/soccer/schedule/_/date/{date_info['current_date']}"
    
    prompt = f"""Visit the ESPN soccer schedule page for {date_info['current_date_readable']} at:
{espn_url}

Extract and provide:

1. COMPLETED MATCHES (games that have finished):
   For each match, provide:
   - Team names
   - Final score
   - Match URL (full ESPN match page URL with gameId)
   
2. UPCOMING MATCHES (games scheduled for today that haven't started yet):
   For each match, provide:
   - Team names
   - Scheduled time (in the timezone shown on ESPN)

Format your response clearly with two sections: "COMPLETED MATCHES" and "UPCOMING MATCHES".
For completed matches, include the match URL.
"""

    print(f"Stage 1a: Extracting current day schedule from {espn_url}...")
    
    response = client.chat.completions.create(
        model="gpt-4o-search-preview",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        max_tokens=2000
    )
    
    return response.choices[0].message.content


def extract_previous_day_schedule(client, date_info):
    """
    Stage 1b: Use search GPT to extract information from ESPN schedule for previous day
    Returns: teams, scores, match URLs for completed games
    """
    espn_url = f"https://www.espn.com/soccer/schedule/_/date/{date_info['previous_date']}"
    
    prompt = f"""Visit the ESPN soccer schedule page for {date_info['previous_date_readable']} at:
{espn_url}

Extract and provide information for COMPLETED MATCHES only (ignore any upcoming matches):

For each completed match, provide:
- Team names
- Final score
- Match URL (full ESPN match page URL with gameId)

Format your response clearly.
"""

    print(f"Stage 1b: Extracting previous day schedule from {espn_url}...")
    
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
    1. Stage 1a: Extract schedule info for current day (completed + upcoming)
    2. Stage 1b: Extract schedule info for previous day (completed only)
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
        print(f"Processing schedule for:")
        print(f"  Current day: {date_info['current_date_readable']}")
        print(f"  Previous day: {date_info['previous_date_readable']}")
        
        # Stage 1a: Current day schedule
        current_day_results = extract_current_day_schedule(client, date_info)
        print(f"\n{'='*60}")
        print(f"CURRENT DAY SCHEDULE ({date_info['current_date_readable']})")
        print(f"{'='*60}")
        print(current_day_results)
        print(f"{'='*60}\n")
        
        # Stage 1b: Previous day schedule
        previous_day_results = extract_previous_day_schedule(client, date_info)
        print(f"\n{'='*60}")
        print(f"PREVIOUS DAY RESULTS ({date_info['previous_date_readable']})")
        print(f"{'='*60}")
        print(previous_day_results)
        print(f"{'='*60}\n")
        
        # Return success
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Schedule extraction completed successfully',
                'current_day_date': date_info['current_date_readable'],
                'previous_day_date': date_info['previous_date_readable']
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e

