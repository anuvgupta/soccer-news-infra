import json
import os
import boto3
from datetime import datetime, timedelta
from openai import OpenAI

sns_client = boto3.client('sns')

def load_prompt_template():
    """Load the prompt template from file"""
    template_path = os.path.join(os.path.dirname(__file__), 'prompt_template.txt')
    with open(template_path, 'r') as f:
        return f.read()

def format_prompt(template: str) -> str:
    """Format the prompt template with current and previous dates"""
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    current_date = today.strftime('%Y%m%d')
    previous_date = yesterday.strftime('%Y%m%d')
    
    return template.replace('{current_date}', current_date).replace('{previous_date}', previous_date)

def handler(event, context):
    """
    Lambda handler that:
    1. Calls OpenAI API with web search enabled
    2. Formats the response into notification format
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
        
        # Load and format prompt
        prompt_template = load_prompt_template()
        formatted_prompt = format_prompt(prompt_template)
        
        # Use Chat Completions API with search-enabled model
        # gpt-4o-search-preview has built-in web search capabilities
        print(f"Calling OpenAI with web search enabled model (gpt-4o-search-preview)...")
        
        response = client.chat.completions.create(
            model="gpt-4o-search-preview",  # This model has web search built-in
            messages=[
                {
                    "role": "system",
                    "content": "You are a soccer news aggregator. Search the web for the latest soccer news and provide accurate, up-to-date information about recent matches, results, and upcoming games. Focus on EPL, MLS, La Liga, and major competitions."
                },
                {
                    "role": "user",
                    "content": formatted_prompt
                }
            ],
            max_tokens=1000
        )
        
        notification_content = response.choices[0].message.content
        
        print(f"Received response from OpenAI: {len(notification_content)} characters")
        
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
        error_message = f"Error processing soccer news: {str(e)}"
        
        # Try to send error notification to SNS if possible
        try:
            sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
            if sns_topic_arn:
                sns_client.publish(
                    TopicArn=sns_topic_arn,
                    Message=error_message,
                    Subject="Soccer News Error"
                )
        except:
            pass
        
        raise e

