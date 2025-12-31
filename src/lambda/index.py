import json
import os
import boto3
from datetime import datetime, timedelta
from openai import OpenAI

sns_client = boto3.client('sns')

def load_prompt_template(template_name):
    """Load a prompt template from file"""
    template_path = os.path.join(os.path.dirname(__file__), template_name)
    with open(template_path, 'r') as f:
        return f.read()

def format_prompt(template: str) -> str:
    """Format the prompt template with current and previous dates"""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    # Formatted dates for ESPN URLs (YYYYMMDD)
    current_date = today.strftime('%Y%m%d')
    previous_date = yesterday.strftime('%Y%m%d')
    
    # Human-readable dates for context
    current_date_readable = today.strftime('%B %d, %Y')  # e.g., "December 30, 2025"
    previous_date_readable = yesterday.strftime('%B %d, %Y')  # e.g., "December 29, 2025"
    
    # Include full timestamp with timezone for accurate time-based filtering
    current_timestamp = today.strftime('%Y-%m-%d %H:%M:%S %Z')
    if not current_timestamp.endswith(' UTC'):
        # Lambda runs in UTC, make it explicit
        current_timestamp = today.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    return (template
            .replace('{current_date}', current_date)
            .replace('{previous_date}', previous_date)
            .replace('{current_date_readable}', current_date_readable)
            .replace('{previous_date_readable}', previous_date_readable)
            .replace('{current_timestamp}', current_timestamp))

def handler(event, context):
    """
    Lambda handler that:
    1. Calls OpenAI API with web search enabled to gather information (Stage 1)
    2. Calls OpenAI API with GPT-4 to format the information (Stage 2)
    3. Publishes to SNS topic
    """
    try:
        # Get environment variables
        sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
        if not sns_topic_arn:
            raise ValueError('SNS_TOPIC_ARN environment variable is not set')
        
        # Get OpenAI API key from environment variable
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError('OPENAI_API_KEY environment variable is not set')
        
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        # STAGE 1: Information Gathering with Search Model
        print("Stage 1: Gathering information with search model...")
        search_template = load_prompt_template('search_prompt.txt')
        search_prompt = format_prompt(search_template)
        
        search_response = client.chat.completions.create(
            model="gpt-4o-search-preview",  # Search-enabled model for gathering info
            messages=[
                {
                    "role": "system",
                    "content": search_prompt
                }
            ],
            max_tokens=4000  # More tokens for comprehensive gathering with player details
        )
        
        gathered_info = search_response.choices[0].message.content
        print(f"Stage 1 complete: Gathered {len(gathered_info)} characters of information")
        print(f"Gathered information:\n\n{gathered_info}\n\n")
        
        # STAGE 2: Format with Reliable Model
        print("Stage 2: Formatting information with GPT-4...")
        format_template = load_prompt_template('format_prompt.txt')
        format_prompt_text = format_prompt(format_template)
        
        format_response = client.chat.completions.create(
            model="gpt-4o",  # More reliable model for formatting
            messages=[
                {
                    "role": "system",
                    "content": format_prompt_text
                },
                {
                    "role": "user",
                    "content": f"Here is the information to format:\n\n{gathered_info}"
                }
            ],
            max_tokens=1000
        )
        
        notification_content = format_response.choices[0].message.content
        print(f"Stage 2 complete: Formatted message is {len(notification_content)} characters")
        print(f"Formatted message:\n\n{notification_content}\n\n")

        
        # Extract headline for SNS subject (first line before triple newline)
        # The LLM should output: [headline]\n\n\n[description]
        if "\n\n\n" in notification_content:
            headline, description = notification_content.split("\n\n\n", 1)
            headline = headline.strip()
            description = description.strip()
        else:
            # Fallback: use first line as headline, rest as description
            lines = notification_content.split("\n", 1)
            headline = lines[0].strip()
            description = lines[1].strip() if len(lines) > 1 else ""
        
        # Sanitize headline for SNS Subject (remove newlines, ensure non-empty)
        # SNS Subject doesn't allow newlines and must not be empty
        headline = headline.replace('\n', ' ').replace('\r', ' ').strip()
        if not headline:
            headline = "Soccer News Update"
        
        # Use the original response as the message (it's already in the correct format)
        message = notification_content.strip()
        
        # Publish to SNS
        response = sns_client.publish(
            TopicArn=sns_topic_arn,
            Message=message,
            Subject=headline[:100]  # SNS subject is limited to 100 chars
        )
        
        print(f"Published message to SNS. MessageId: {response['MessageId']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Notification sent successfully',
                'messageId': response['MessageId'],
                'headline': headline,
                'descriptionLength': len(description)
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        # Errors are logged to CloudWatch, no need to notify subscribers
        raise e

