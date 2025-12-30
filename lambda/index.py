import json
import os
import time
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
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        if not sns_topic_arn:
            raise ValueError('SNS_TOPIC_ARN environment variable is not set')
        
        if not openai_api_key:
            raise ValueError('OPENAI_API_KEY environment variable is not set')
        
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        # Load and format prompt
        prompt_template = load_prompt_template()
        formatted_prompt = format_prompt(prompt_template)
        
        # Use OpenAI Assistants API with web search enabled
        # This is the recommended way to enable web search with OpenAI
        print(f"Creating assistant with web search enabled...")
        
        notification_content = None
        assistant_id = None
        
        try:
            # Try to use Assistants API with web search
            # Using gpt-4o for better compatibility with web search
            assistant = client.beta.assistants.create(
                name="Soccer News Aggregator",
                instructions=formatted_prompt,
                model="gpt-4o",  # gpt-4o supports web search in Assistants API
                tools=[{"type": "web_search"}],  # Enable web search
                temperature=0.7
            )
            assistant_id = assistant.id
            print(f"Assistant created: {assistant_id}")
            
            # Create a thread and run the assistant
            thread = client.beta.threads.create()
            
            # Add the user message to the thread
            message = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content="Please search for the latest soccer news and create the notification as specified in the instructions."
            )
            
            # Run the assistant
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )
            
            print(f"Run started: {run.id}, status: {run.status}")
            
            # Wait for the run to complete
            max_wait_time = 300  # 5 minutes max
            start_time = time.time()
            
            while run.status in ['queued', 'in_progress', 'cancelling']:
                if time.time() - start_time > max_wait_time:
                    raise TimeoutError("Assistant run timed out")
                time.sleep(2)
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                print(f"Run status: {run.status}")
            
            if run.status != 'completed':
                raise Exception(f"Assistant run failed with status: {run.status}")
            
            # Retrieve the messages from the thread
            messages = client.beta.threads.messages.list(thread_id=thread.id)
            
            # Get the assistant's response (most recent message)
            for message in messages.data:
                if message.role == 'assistant' and message.content:
                    # Get text content from the message
                    if hasattr(message.content[0], 'text'):
                        notification_content = message.content[0].text.value
                        break
            
            if not notification_content:
                raise Exception("No response received from assistant")
                
        except Exception as e:
            print(f"Assistants API failed: {str(e)}, falling back to Chat Completions API")
            # Fallback to regular Chat Completions API
            # Note: This won't have web search, but will use the model's training data
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a soccer news aggregator. Use your knowledge to provide accurate information about recent soccer matches, results, and upcoming games. Focus on EPL, MLS, La Liga, and major competitions."
                    },
                    {
                        "role": "user",
                        "content": formatted_prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            notification_content = response.choices[0].message.content
        finally:
            # Clean up: delete the assistant if it was created
            if assistant_id:
                try:
                    client.beta.assistants.delete(assistant_id)
                except:
                    pass
        
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

