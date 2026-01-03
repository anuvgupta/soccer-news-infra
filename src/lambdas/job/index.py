import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from openai import OpenAI
import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


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


def load_standings_urls():
    """
    Load standings URLs from competition_standings_urls.txt file
    
    Returns:
        dict: Mapping of competition names to standings URLs
              e.g., {"English Premier League": "https://..."}
    """
    standings_file = os.path.join(os.path.dirname(__file__), 'competition_standings_urls.txt')
    standings_mapping = {}
    
    try:
        with open(standings_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Parse format: "Competition Name - URL"
                if ' - ' in line:
                    parts = line.split(' - ', 1)
                    competition_name = parts[0].strip()
                    url = parts[1].strip()
                    standings_mapping[competition_name] = url
        
        print(f"Loaded {len(standings_mapping)} standings URLs from {standings_file}")
        return standings_mapping
        
    except FileNotFoundError:
        print(f"Warning: {standings_file} not found")
        return {}
    except Exception as e:
        print(f"Error loading standings URLs: {e}")
        return {}


def fetch_match_report(match_data):
    """
    Fetch the match report page for a given match
    
    Args:
        match_data: Match dict containing 'match_url' field
    
    Returns:
        str: HTML content from Story__Body class, or empty string if error
    """
    try:
        match_url = match_data.get('match_url', '')
        if not match_url:
            print(f"No match_url found for match: {match_data.get('team1')} vs {match_data.get('team2')}")
            return ''
        
        # Extract match ID from URL
        # Example: https://www.espn.com/soccer/match/_/gameId/740778 -> 740778
        match_id = match_url.rstrip('/').split('/')[-1]
        
        # Build report URL
        report_url = f"https://www.espn.com/soccer/report/_/gameId/{match_id}"
        
        print(f"Fetching report for {match_data.get('team1')} vs {match_data.get('team2')} from {report_url}")
        
        # Call browser lambda to extract Story__Body class
        html = invoke_browser_lambda(
            url=report_url,
            operation='find_classes',
            keyword='Story__Body'
        )
        
        return html
        
    except Exception as e:
        print(f"Error fetching report for match {match_data.get('team1')} vs {match_data.get('team2')}: {e}")
        return ''


def fetch_reports_in_batches(matches, batch_size=10):
    """
    Fetch match reports for all matches in parallel batches
    
    Args:
        matches: List of match dicts
        batch_size: Number of matches to process in parallel (default: 10)
    
    Returns:
        list: Matches with 'report' field added
    """
    if not matches:
        return matches
    
    print(f"\nFetching reports for {len(matches)} matches in batches of {batch_size}...")
    
    # Process matches in batches
    enriched_matches = []
    
    for i in range(0, len(matches), batch_size):
        batch = matches[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(matches) + batch_size - 1) // batch_size
        
        print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} matches)...")
        
        # Use ThreadPoolExecutor to fetch reports in parallel
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            # Submit all tasks
            future_to_match_data = {executor.submit(fetch_match_report, match_data): match_data for match_data in batch}
            
            # Collect results as they complete
            for future in as_completed(future_to_match_data):
                match_data = future_to_match_data[future]
                try:
                    report_html = future.result()
                    match_data['report'] = report_html
                    print(f"  ✓ Report fetched for {match_data.get('team1')} vs {match_data.get('team2')} ({len(report_html)} chars)")
                except Exception as e:
                    print(f"  ✗ Failed to fetch report for {match_data.get('team1')} vs {match_data.get('team2')}: {e}")
                    match_data['report'] = ''
                
                enriched_matches.append(match_data)
    
    print(f"\nCompleted fetching reports for {len(enriched_matches)} matches")
    return enriched_matches


def fetch_standings_in_parallel(standings_urls):
    """
    Fetch standings HTML for all competitions in parallel
    
    Args:
        standings_urls: List of dicts with 'competition' and 'url' keys
                       e.g., [{"competition": "English Premier League", "url": "https://..."}]
    
    Returns:
        list: Standings data with HTML content added
              e.g., [{"competition": "...", "url": "...", "html": "..."}]
    """
    if not standings_urls:
        return []
    
    print(f"\nFetching standings for {len(standings_urls)} competitions in parallel...")
    
    def fetch_single_standing(standing_data):
        """Fetch standings HTML for a single competition"""
        try:
            competition = standing_data.get('competition', '')
            url = standing_data.get('url', '')
            
            print(f"Fetching standings for {competition} from {url}")
            
            # Call browser lambda to extract standings__table class
            html = invoke_browser_lambda(
                url=url,
                operation='find_classes',
                keyword='standings__table'
            )
            
            return {
                'competition': competition,
                'url': url,
                'html': html
            }
            
        except Exception as e:
            print(f"Error fetching standings for {standing_data.get('competition')}: {e}")
            return {
                'competition': standing_data.get('competition', ''),
                'url': standing_data.get('url', ''),
                'html': ''
            }
    
    # Use ThreadPoolExecutor to fetch all standings in parallel
    enriched_standings = []
    with ThreadPoolExecutor(max_workers=len(standings_urls)) as executor:
        # Submit all tasks
        future_to_standing = {executor.submit(fetch_single_standing, standing): standing for standing in standings_urls}
        
        # Collect results as they complete
        for future in as_completed(future_to_standing):
            try:
                standing_data = future.result()
                enriched_standings.append(standing_data)
                print(f"  ✓ Standings fetched for {standing_data.get('competition')} ({len(standing_data.get('html', ''))} chars)")
            except Exception as e:
                standing = future_to_standing[future]
                print(f"  ✗ Failed to fetch standings for {standing.get('competition')}: {e}")
                enriched_standings.append({
                    'competition': standing.get('competition', ''),
                    'url': standing.get('url', ''),
                    'html': ''
                })
    
    print(f"\nCompleted fetching standings for {len(enriched_standings)} competitions")
    return enriched_standings


def extract_matches_with_gpt(client, html_content, date_str, standings_mapping=None):
    """
    Use GPT-4o to extract match data from HTML
    
    Args:
        client: OpenAI client instance
        html_content: HTML content (already truncated)
        date_str: Date string for context (e.g., "January 1, 2025")
        standings_mapping: Optional dict mapping competition names to standings URLs
    
    Returns:
        dict: Match data with structure defined in prompt, including standings_urls array
    """
    # Load relevant competitions from file
    competitions_file = os.path.join(os.path.dirname(__file__), 'competitions.txt')
    try:
        with open(competitions_file, 'r') as f:
            competitions = [line.strip() for line in f if line.strip()]
        competitions_list = '\n'.join([f"- {comp}" for comp in competitions])
        print(f"Loaded {len(competitions)} relevant competitions from {competitions_file}")
    except FileNotFoundError:
        print(f"Warning: {competitions_file} not found, processing all competitions")
        competitions_list = "- (All competitions)"
        competitions = []
    
    # Build prompt with competition filter
    competitions_instruction = ""
    if competitions:
        competitions_instruction = f"""
IMPORTANT: Only extract matches from these relevant competitions:
{competitions_list}

Ignore all other competitions/leagues not listed above.
"""
    
    # Build standings URLs section if provided
    standings_instruction = ""
    standings_urls_format = ""
    if standings_mapping:
        standings_list = '\n'.join([f"- {comp}: {url}" for comp, url in standings_mapping.items()])
        standings_instruction = f"""
STANDINGS URLS AVAILABLE:
{standings_list}

After extracting matches, identify which competitions had matches and include their standings URLs.
"""
        standings_urls_format = """,
  "standings_urls": [
    {{
      "competition": "English Premier League",
      "url": "https://www.espn.com/soccer/standings/_/league/eng.1"
    }}
  ]"""
    
    prompt = f"""Extract all soccer matches (both completed and upcoming) from this ESPN schedule HTML for {date_str}.

Each section has a league/competition name in the Table__Title div. For each match, extract:
- league: The league/competition name from the Table__Title (e.g., "English Premier League", "Africa Cup of Nations")
- team1: The first team name shown
- team2: The second team name shown
- score: The final score in format "X-Y" (e.g., "1-3") where X is team1's score and Y is team2's score
  * If NO score is available (match hasn't started yet), use "upcoming" as the score value
- match_url: The ESPN match page URL (format: https://www.espn.com/soccer/match/_/gameId/######)

{competitions_instruction}

{standings_instruction}

Do NOT determine the winner - just extract the league, team names, score, and URL exactly as shown.

Return JSON with this exact structure:
{{
  "matches": [
    {{
      "league": "English Premier League",
      "team1": "Burnley",
      "team2": "Newcastle United",
      "score": "1-3",
      "match_url": "https://www.espn.com/soccer/match/_/gameId/740778"
    }},
    {{
      "league": "La Liga",
      "team1": "Real Madrid",
      "team2": "Barcelona",
      "score": "upcoming",
      "match_url": "https://www.espn.com/soccer/match/_/gameId/740779"
    }}
  ]{standings_urls_format}
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
    
    # Calculate the winner for each match based on the score
    matches = result.get('matches', [])
    for match_data in matches:
        score = match_data.get('score', '')
        
        # Handle upcoming matches (no score available yet)
        if score.lower() == 'upcoming':
            match_data['winner'] = 'Upcoming'
        elif '-' in score:
            try:
                parts = score.split('-')
                team1_score = int(parts[0].strip())
                team2_score = int(parts[1].strip())
                
                if team1_score > team2_score:
                    match_data['winner'] = match_data['team1']
                elif team2_score > team1_score:
                    match_data['winner'] = match_data['team2']
                else:
                    match_data['winner'] = 'Draw'
            except (ValueError, IndexError):
                # If we can't parse the score, set winner as unknown
                match_data['winner'] = 'Unknown'
        else:
            match_data['winner'] = 'Unknown'
    
    completed_count = sum(1 for m in matches if m.get('winner') not in ['Upcoming', 'Unknown'])
    upcoming_count = sum(1 for m in matches if m.get('winner') == 'Upcoming')
    print(f"GPT-4o extracted {len(matches)} matches ({completed_count} completed, {upcoming_count} upcoming), winners calculated in Python")
    
    return result


def summarize_for_sms(client, matches_data, date_str, standings_data=None):
    """
    Use GPT-4o to summarize match results into an SMS notification format
    
    Args:
        client: OpenAI client instance
        matches_data: List of match dictionaries with reports
        date_str: Date string for context (e.g., "December 31, 2024")
        standings_data: Optional list of standings dicts with HTML content
    
    Returns:
        str: Formatted SMS notification with headline, description, and standings summary
    """
    if not matches_data:
        return "No matches found for this date."
    
    # Prepare match data for summarization (exclude long HTML reports from prompt)
    matches_summary = []
    for match in matches_data:
        match_info = {
            'league': match.get('league', ''),
            'team1': match.get('team1', ''),
            'team2': match.get('team2', ''),
            'score': match.get('score', ''),
            'winner': match.get('winner', '')
        }
        # Include a truncated version of the report for context
        report = match.get('report', '')
        if report and len(report) > 15000:
            match_info['report_excerpt'] = report[:15000] + '...'
        elif report:
            match_info['report_excerpt'] = report
        else:
            match_info['report_excerpt'] = 'No report available'
        
        matches_summary.append(match_info)
    
    # Prepare standings data if provided
    standings_section = ""
    if standings_data:
        standings_summary = []
        for standing in standings_data:
            standing_info = {
                'competition': standing.get('competition', ''),
                'url': standing.get('url', '')
            }
            # Include a truncated version of the HTML for context
            html = standing.get('html', '')
            if html and len(html) > 20000:
                standing_info['html_excerpt'] = html[:20000] + '...'
            elif html:
                standing_info['html_excerpt'] = html
            else:
                standing_info['html_excerpt'] = 'No standings data available'
            
            standings_summary.append(standing_info)
        
        standings_section = f"""

STANDINGS DATA:
{json.dumps(standings_summary, indent=2)}

The standings HTML contains table data showing team positions, points, wins, losses, draws, goals for/against, etc.
Use this data to provide current standings context in your description and create a separate standings summary."""
    
    prompt = f"""You are creating an SMS notification for soccer match results and upcoming matches from {date_str}.

MATCH DATA:
{json.dumps(matches_summary, indent=2)}

Note: Matches with score="upcoming" and winner="Upcoming" have not been played yet.{standings_section}

CRITICAL: Only use information from the match data provided above. Do NOT make up or invent any matches, upcoming or otherwise. If there are no upcoming matches in the data, do not mention upcoming matches at all.

Create an SMS notification with this EXACT format:

1. HEADLINE (first line):
   - Maximum 100 characters (HARD LIMIT - must fit on iPhone lock screen)
   - Focus on the most significant event(s): finals, semifinals, major upsets, surprising wins, popular teams (e.g., Real Madrid, Barcelona, Manchester United, Liverpool, etc.), or significant knockouts
   - Be specific and compelling
   - Examples: "Real Madrid wins 3-1 in Champions League semifinal", "Liverpool upset 2-0 by underdog Burnley"

2. THREE BLANK LINES after headline (just newlines, no text)

3. DESCRIPTION (max 8 sentences, max 100 words):
   - NOT overly verbose - speak quickly and plainly
   - Use short, direct sentences
   - First, expand on the headline event with more details
   - Then cover other significant completed matches from the day
   - When relevant, include current standings context (e.g., "moves them to 2nd place", "extends their lead at the top")
   - ONLY if there are actual upcoming matches in the provided data (score="upcoming"), mention them at the end
   - Do NOT invent or make up upcoming matches that are not in the provided match data
   - Do NOT omit any key events or results
   - Separate different topics/leagues with one blank line
   - Focus on outcomes and significance, not flowery language
   - CRITICAL: Maximum 8 sentences and 100 words total

4. THREE BLANK LINES after description (just newlines, no text)

5. STANDINGS SUMMARY (if standings data provided):
   - Start with "STANDINGS:" on its own line
   - For each competition that had matches, provide a brief plain-text summary of the current standings
   - Focus on top teams (top 3-5) and their points
   - Mention any tight races or significant gaps
   - Use concise, readable prose format
   - Separate different competitions with one blank line

FORMAT REQUIREMENTS:
- Return ONLY the formatted notification text
- No labels like "HEADLINE:" or "DESCRIPTION:" (except "STANDINGS:" for the standings section)
- Exactly 3 newlines between headline and description
- Maximum 8 sentences and 100 words in the description
- Exactly 3 newlines between description and standings section

Example format:
Manchester United advances to FA Cup final with 2-1 win


United's dramatic late goal secured their spot in the final against Arsenal. The match was tied 1-1 until the 88th minute.

In the Premier League, Liverpool defeated Chelsea 3-0 to move into second place. Mohamed Salah scored twice in the first half.

Barcelona drew 1-1 with Atletico Madrid in La Liga. The result keeps Barcelona at the top of the table with a 5-point lead.


STANDINGS:
English Premier League: Arsenal leads with 45 points, followed by Manchester City (43) and Liverpool (41). Chelsea sits in 4th with 38 points. The race for Champions League qualification remains tight with just 3 points separating 3rd through 6th place.

La Liga: Barcelona sits atop the table with 48 points, 5 clear of Real Madrid in second. Atletico Madrid holds 3rd with 38 points."""

    print(f"Sending match data to GPT-4o for SMS summarization...")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        max_tokens=1500,
        temperature=0.7
    )
    
    sms_notification = response.choices[0].message.content.strip()
    
    print(f"GPT-4o generated SMS notification ({len(sms_notification)} characters)")
    
    return sms_notification


def send_to_discord(webhook_url, message):
    """
    Send a message to Discord via webhook
    
    Args:
        webhook_url: Discord webhook URL
        message: Message content to send
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        payload = {
            "content": message
        }
        
        print(f"Sending message to Discord webhook...")
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code in [200, 204]:
            print(f"✓ Successfully sent message to Discord")
            return True
        else:
            print(f"✗ Discord webhook returned status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error sending to Discord: {e}")
        return False


def parse_timestamp(timestamp_input, timezone):
    """
    Parse various timestamp formats into a datetime object in the specified timezone
    
    Args:
        timestamp_input: Can be:
            - YYYYMMDD format string (e.g., "20241231")
            - ISO format string (e.g., "2024-12-31" or "2024-12-31T00:00:00")
            - Unix timestamp in seconds (int or string)
        timezone: ZoneInfo timezone object
    
    Returns:
        datetime: Parsed datetime in the specified timezone
    """
    # If it's an integer or numeric string, treat as Unix timestamp
    if isinstance(timestamp_input, int):
        return datetime.fromtimestamp(timestamp_input, tz=timezone)
    
    timestamp_str = str(timestamp_input).strip()
    
    # Try to parse as Unix timestamp (numeric string)
    try:
        unix_ts = float(timestamp_str)
        return datetime.fromtimestamp(unix_ts, tz=timezone)
    except ValueError:
        pass
    
    # Try to parse as YYYYMMDD format
    if len(timestamp_str) == 8 and timestamp_str.isdigit():
        try:
            dt = datetime.strptime(timestamp_str, '%Y%m%d')
            return dt.replace(tzinfo=timezone)
        except ValueError:
            pass
    
    # Try to parse as ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
    try:
        # Handle date only (YYYY-MM-DD)
        if 'T' not in timestamp_str and len(timestamp_str) == 10:
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d')
            return dt.replace(tzinfo=timezone)
        # Handle datetime with T separator
        elif 'T' in timestamp_str:
            # Try with seconds
            try:
                dt = datetime.fromisoformat(timestamp_str)
                # Convert to target timezone if it has tzinfo, otherwise assume it's in target timezone
                if dt.tzinfo:
                    return dt.astimezone(timezone)
                else:
                    return dt.replace(tzinfo=timezone)
            except ValueError:
                pass
    except ValueError:
        pass
    
    raise ValueError(f"Unable to parse timestamp: {timestamp_input}. "
                     f"Supported formats: YYYYMMDD (20241231), ISO (2024-12-31), or Unix timestamp (1735689600)")


def handler(event, context):
    """
    Lambda handler - simplified flow:
    1. Get target date (from input or default to current time in Pacific time)
    2. Calculate both today and yesterday dates
    3. Build ESPN schedule URLs for both dates and fetch HTML via Browser Lambda in parallel
    4. Combine HTML from both days and truncate to relevant section
    5. Extract match data using GPT-4o
    6. Fetch match reports in parallel (batches of 10)
    7. Generate SMS notification and print JSON results to console
    
    Event parameters:
        timestamp (optional): Custom date to use as "today". Supports:
            - YYYYMMDD format (e.g., "20241231")
            - ISO format (e.g., "2024-12-31" or "2024-12-31T00:00:00")
            - Unix timestamp in seconds (e.g., 1735689600)
        If not provided, uses current time in Pacific time as "today".
        Yesterday is calculated as exactly 24 hours before "today".
    """
    try:
        # Get OpenAI API key from environment variable
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError('OPENAI_API_KEY environment variable is not set')
        
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        # 1. Get target date (from input or default to current time in Pacific time)
        pacific_tz = ZoneInfo("America/Los_Angeles")
        
        # Check if a custom timestamp was provided in the event
        custom_timestamp = event.get('timestamp') if isinstance(event, dict) else None
        
        if custom_timestamp:
            print(f"Using custom timestamp: {custom_timestamp}")
            today_date = parse_timestamp(custom_timestamp, pacific_tz)
        else:
            # Default behavior: use current time in Pacific time
            today_date = datetime.now(pacific_tz)
            print("No custom timestamp provided, using current time in Pacific time")
        
        # Calculate yesterday (exactly 24 hours before today)
        yesterday_date = today_date - timedelta(days=1)
        
        # Format both dates
        today = today_date.strftime('%Y%m%d')
        today_readable = today_date.strftime('%B %d, %Y')
        yesterday = yesterday_date.strftime('%Y%m%d')
        yesterday_readable = yesterday_date.strftime('%B %d, %Y')
        
        print(f"Processing soccer matches for: {yesterday_readable} and {today_readable}")
        print("=" * 60)
        
        # Load standings URLs mapping
        standings_mapping = load_standings_urls()
        
        # 2. Build URLs for both dates and fetch HTML via Browser Lambda in parallel
        yesterday_url = f"https://www.espn.com/soccer/schedule/_/date/{yesterday}"
        today_url = f"https://www.espn.com/soccer/schedule/_/date/{today}"
        
        print(f"\nFetching HTML from both dates in parallel:")
        print(f"  Yesterday: {yesterday_url}")
        print(f"  Today: {today_url}")
        print(f"Operation: find_classes, Keyword: ScheduleTables")
        
        # Use ThreadPoolExecutor to fetch both URLs in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_yesterday = executor.submit(
                invoke_browser_lambda,
                yesterday_url,
                'find_classes',
                'ScheduleTables'
            )
            future_today = executor.submit(
                invoke_browser_lambda,
                today_url,
                'find_classes',
                'ScheduleTables'
            )
            
            # Get results from both futures
            html_yesterday = future_yesterday.result()
            html_today = future_today.result()
        
        print(f"\nReceived HTML from yesterday: {len(html_yesterday)} characters")
        print(f"Received HTML from today: {len(html_today)} characters")
        
        # 3. Truncate each HTML separately (full 50K budget per day)
        truncated_html_yesterday = html_yesterday[:50000]
        truncated_html_today = html_today[:50000]
        
        # 4. Extract match data using GPT-4o (parallel calls for both days)
        print("\nExtracting match data with GPT-4o (parallel calls for both days)...")
        
        # Parallel GPT extraction
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_yesterday = executor.submit(
                extract_matches_with_gpt,
                client,
                truncated_html_yesterday,
                yesterday_readable,
                standings_mapping
            )
            future_today = executor.submit(
                extract_matches_with_gpt,
                client,
                truncated_html_today,
                today_readable,
                standings_mapping
            )
            
            # Get results from both futures
            result_yesterday = future_yesterday.result()
            result_today = future_today.result()
        
        # Combine matches from both days
        matches_yesterday = result_yesterday.get('matches', [])
        matches_today = result_today.get('matches', [])
        all_matches = matches_yesterday + matches_today
        
        # Combine standings URLs from both days (remove duplicates)
        standings_urls_yesterday = result_yesterday.get('standings_urls', [])
        standings_urls_today = result_today.get('standings_urls', [])
        all_standings_urls = standings_urls_yesterday + standings_urls_today
        
        # Remove duplicate standings URLs based on competition name
        unique_standings = {}
        for standing in all_standings_urls:
            comp = standing.get('competition', '')
            if comp and comp not in unique_standings:
                unique_standings[comp] = standing
        
        unique_standings_urls = list(unique_standings.values())
        
        result = {
            'matches': all_matches
        }
        
        print(f"Extracted {len(matches_yesterday)} matches from yesterday, {len(matches_today)} matches from today (total: {len(all_matches)})")
        
        # 5. Fetch match reports for completed matches only
        matches = result.get('matches', [])
        if matches:
            # Separate completed and upcoming matches
            completed_matches = [m for m in matches if m.get('winner') not in ['Upcoming', 'Unknown']]
            upcoming_matches = [m for m in matches if m.get('winner') == 'Upcoming']
            
            print(f"\nFound {len(matches)} total matches ({len(completed_matches)} completed, {len(upcoming_matches)} upcoming)")
            
            # Only fetch reports for completed matches
            if completed_matches:
                print(f"Fetching reports for {len(completed_matches)} completed matches...")
                enriched_completed = fetch_reports_in_batches(completed_matches, batch_size=10)
            else:
                enriched_completed = []
            
            # Add empty reports for upcoming matches
            for match in upcoming_matches:
                match['report'] = ''
            
            # Combine all matches back together
            result['matches'] = enriched_completed + upcoming_matches
        else:
            print("\nNo matches found, skipping report fetching")
        
        # 5.5. Fetch standings HTML for relevant competitions
        print(f"\nFound {len(unique_standings_urls)} unique competitions with matches")
        if unique_standings_urls:
            enriched_standings = fetch_standings_in_parallel(unique_standings_urls)
            result['standings'] = enriched_standings
        else:
            print("\nNo standings URLs to fetch")
            result['standings'] = []
        
        # 6. Generate SMS notification summary
        print("\n" + "=" * 60)
        print("GENERATING SMS NOTIFICATION...")
        print("=" * 60)
        
        date_range_str = f"{yesterday_readable} and {today_readable}"
        sms_notification = summarize_for_sms(client, result.get('matches', []), date_range_str, result.get('standings', []))
        result['sms_notification'] = sms_notification
        
        print("\n" + "=" * 60)
        print("SMS NOTIFICATION:")
        print("=" * 60)
        print(sms_notification)
        print("=" * 60)
        
        # Send to Discord webhook
        discord_webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
        if discord_webhook_url:
            print("\n" + "=" * 60)
            print("SENDING TO DISCORD...")
            print("=" * 60)
            discord_success = send_to_discord(discord_webhook_url, sms_notification)
            result['discord_sent'] = discord_success
        else:
            print("\nDISCORD_WEBHOOK_URL not set, skipping Discord notification")
        
        # 7. Print JSON results to console
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
