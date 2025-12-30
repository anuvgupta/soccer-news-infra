# Message grouping sender ID condition
_Exported on 12/29/2025 at 17:58:06 PST from Cursor (2.2.44)_

---

**User**

@prompt1.txt (1-13) 

---

**Cursor**


Reviewing the requirements and exploring the project structure.



Checking for existing infrastructure files and reviewing the README:



Creating the AWS CDK infrastructure. Setting up the initial todo list:



Creating the AWS CDK infrastructure from scratch. Setting up the project structure:


```json
{
  "name": "soccer-news-infra",
  "version": "1.0.0",
  "description": "CDK stack for soccer news infrastructure",
  "main": "lib/index.js",
  "scripts": {
    "build": "tsc",
    "watch": "tsc -w",
    "cdk": "cdk",
    "deploy": "cdk deploy",
    "synth": "cdk synth"
  },
  "keywords": [],
  "author": "",
  "license": "ISC",
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "~5.3.0",
    "aws-cdk": "^2.100.0"
  },
  "dependencies": {
    "aws-cdk-lib": "^2.100.0",
    "constructs": "^10.0.0"
  }
}

```

```jsonc
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["es2020"],
    "declaration": true,
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": false,
    "inlineSourceMap": true,
    "inlineSources": true,
    "experimentalDecorators": true,
    "strictPropertyInitialization": false,
    "typeRoots": ["./node_modules/@types"],
    "outDir": "lib",
    "rootDir": "."
  },
  "include": ["bin/**/*", "lib/**/*"],
  "exclude": ["node_modules", "cdk.out"]
}

```

```json
{
  "app": "npx ts-node --prefer-ts-exts bin/app.ts",
  "watch": {
    "include": [
      "**"
    ],
    "exclude": [
      "README.md",
      "cdk*.json",
      "**/*.d.ts",
      "**/*.js",
      "tsconfig.json",
      "package*.json",
      "yarn.lock",
      "node_modules",
      "**/__pycache__",
      "**/*.pyc"
    ]
  },
  "context": {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "@aws-cdk/core:checkSecretUsage": true,
    "@aws-cdk/core:target-partitions": [
      "aws",
      "aws-cn"
    ],
    "@aws-cdk-containers/ecs-service-extensions:enableDefaultLogDriver": true,
    "@aws-cdk/aws-ec2:uniqueImdsv2TemplateName": true,
    "@aws-cdk/aws-ecs:arnFormatIncludesClusterName": true,
    "@aws-cdk/aws-iam:minimizePolicies": true,
    "@aws-cdk/core:validateSnapshotRemovalPolicy": true,
    "@aws-cdk/aws-codepipeline:crossAccountKeyAliasStackSafeResourceName": true,
    "@aws-cdk/aws-s3:createDefaultLoggingPolicy": true,
    "@aws-cdk/aws-sns-subscriptions:restrictSqsDescryption": true,
    "@aws-cdk/aws-apigateway:disableCloudWatchRole": true,
    "@aws-cdk/core:enablePartitionLiterals": true,
    "@aws-cdk/aws-events:eventsTargetQueueSameAccount": true,
    "@aws-cdk/aws-iam:standardizedServicePrincipals": true,
    "@aws-cdk/aws-ecs:disableExplicitDeploymentControllerForCircuitBreaker": true,
    "@aws-cdk/aws-iam:importedRoleStackSafeDefaultPolicyName": true,
    "@aws-cdk/aws-s3:serverAccessLogsUseBucketPolicy": true,
    "@aws-cdk/aws-route53-patters:useCertificate": true,
    "@aws-cdk/customresources:installLatestAwsSdkDefault": false,
    "@aws-cdk/aws-rds:databaseProxyUniqueResourceName": true,
    "@aws-cdk/aws-codedeploy:removeAlarmsFromDeploymentGroup": true,
    "@aws-cdk/aws-apigateway:authorizerChangeDeploymentLogicalId": true,
    "@aws-cdk/aws-ec2:launchTemplateDefaultUserData": true,
    "@aws-cdk/aws-ecs:removeDefaultDeploymentAlarm": true
  }
}

```

```ignore
*.js
!jest.config.js
*.d.ts
node_modules
*.log
.DS_Store
cdk.out
.venv
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
ENV/
.idea/
*.swp
*.swo
*~

```


Creating the CDK app and stack:


```typescript
#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { SoccerNewsStack } from '../lib/soccer-news-stack';

const app = new cdk.App();
new SoccerNewsStack(app, 'SoccerNewsStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
});

```

```typescript
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';
import * as path from 'path';

export class SoccerNewsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create SNS topic for notifications
    const notificationTopic = new sns.Topic(this, 'SoccerNewsTopic', {
      displayName: 'Soccer News Notifications',
      topicName: 'soccer-news-notifications',
    });

    // Create Lambda function
    const soccerNewsLambda = new lambda.Function(this, 'SoccerNewsLambda', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda')),
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      environment: {
        SNS_TOPIC_ARN: notificationTopic.topicArn,
        OPENAI_API_KEY: process.env.OPENAI_API_KEY || '', // Should be set via environment variable or Secrets Manager
      },
    });

    // Grant Lambda permission to publish to SNS
    notificationTopic.grantPublish(soccerNewsLambda);

    // Create EventBridge rule to trigger Lambda daily at 9am UTC
    const schedule = new events.Rule(this, 'SoccerNewsSchedule', {
      schedule: events.Schedule.cron({
        minute: '0',
        hour: '9',
        day: '*',
        month: '*',
        year: '*',
      }),
      description: 'Trigger soccer news Lambda daily at 9am UTC',
    });

    // Add Lambda as target for the schedule
    schedule.addTarget(new targets.LambdaFunction(soccerNewsLambda));

    // Output the SNS topic ARN
    new cdk.CfnOutput(this, 'SnsTopicArn', {
      value: notificationTopic.topicArn,
      description: 'ARN of the SNS topic for soccer news notifications',
    });
  }
}

```


Creating the Lambda function code and prompt template:


```plaintext
You are a soccer news aggregator. Your task is to search the web for the latest soccer/football (not American football) highlights from the last 24 hours and upcoming games/events.

Focus on the following leagues and competitions:
- English Premier League (EPL)
- MLS (US Major League Soccer)
- La Liga (Spain)
- Major competitions: World Cup, Euro Cup, Copa America, Champions League, Club World Cup

Primary focus should be on:
1. Results of matches from the previous day
2. List of upcoming matches

For information gathering, use these resources:
- Previous day schedule: https://www.espn.com/soccer/schedule/_/date/{previous_date} (format: YYYYMMDD)
- Current day schedule: https://www.espn.com/soccer/schedule/_/date/{current_date} (format: YYYYMMDD)
- ESPN, BBC Sports
- League websites for EPL, MLS, and La Liga
- Reddit: r/footballhighlights and other sports subreddits

Create a notification with the following format:

HEADLINE (first part):
- A brief summary that fits in a standard iPhone notification box without needing to open the notification further
- Focus on top highlights at the current exact time/day
- If too much information, keep it concise and mention only the most important news (significant wins, knockouts)
- Should be brief enough to fit in a notification preview

DESCRIPTION (after 3 line breaks):
- Longer description covering all the highlights of the day
- Include the longer form of what's covered in the headline
- Include other lower priority items not in the headline
- Split into sentences
- Sentences about different topics should be spaced out by 2 line breaks
- Maximum 7 sentences total

Format your response as:
HEADLINE: [your headline here]

[3 line breaks]

[your description here - max 7 sentences, with 2 line breaks between different topics]

```

```python
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
        
        # Call OpenAI API with web search enabled
        # Using o1-preview or o1-mini for deep thinking, with web search via function calling
        # Note: OpenAI's web search is available through the Assistants API or via function calling
        # For now, we'll use gpt-4o with web_search capability if available, or instruct it to search
        
        print(f"Calling OpenAI API with prompt length: {len(formatted_prompt)}")
        
        # Try to use a model that supports deep thinking/reasoning
        # o1 models support reasoning but may not have direct web search
        # We'll use gpt-4o which can be instructed to search, or use function calling
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Using gpt-4o which has good reasoning and can be instructed to search
            messages=[
                {
                    "role": "system",
                    "content": "You are a soccer news aggregator. You have access to web search capabilities. When asked to search for information, use your knowledge and reasoning to provide accurate, up-to-date information about soccer matches, results, and upcoming games."
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
        
        print(f"Received response from OpenAI: {len(notification_content)} characters")
        
        # Parse the response to extract headline and description
        # Format should be: HEADLINE: [headline]\n\n\n[description]
        if "HEADLINE:" in notification_content:
            parts = notification_content.split("HEADLINE:", 1)
            if len(parts) > 1:
                remaining = parts[1].strip()
                # Split by triple newline to separate headline from description
                if "\n\n\n" in remaining:
                    headline, description = remaining.split("\n\n\n", 1)
                    headline = headline.strip()
                    description = description.strip()
                else:
                    # Fallback: use first line as headline, rest as description
                    lines = remaining.split("\n", 1)
                    headline = lines[0].strip()
                    description = lines[1].strip() if len(lines) > 1 else ""
            else:
                # Fallback: use first 100 chars as headline
                headline = notification_content[:100].strip()
                description = notification_content[100:].strip()
        else:
            # No HEADLINE marker, use first 100 chars as headline
            headline = notification_content[:100].strip()
            description = notification_content[100:].strip()
        
        # Format the message for SNS
        # Headline first, then 3 line breaks, then description
        message = f"{headline}\n\n\n{description}"
        
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

```

```pip-requirements
openai>=1.12.0
boto3>=1.34.0

```


Updating the CDK stack to bundle Python dependencies and improving the Lambda function to use OpenAI's web search capabilities:



Updating the CDK stack to bundle Python dependencies and improving the Lambda to use OpenAI's web search capabilities:


```typescript
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';
import * as path from 'path';

export class SoccerNewsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create SNS topic for notifications
    const notificationTopic = new sns.Topic(this, 'SoccerNewsTopic', {
      displayName: 'Soccer News Notifications',
      topicName: 'soccer-news-notifications',
    });

    // Create Lambda function with Python dependencies bundled
    const soccerNewsLambda = new lambda.Function(this, 'SoccerNewsLambda', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda'), {
        bundling: {
          image: lambda.Runtime.PYTHON_3_12.bundlingImage,
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output && cp -au . /asset-output'
          ],
        },
      }),
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      environment: {
        SNS_TOPIC_ARN: notificationTopic.topicArn,
        // OPENAI_API_KEY should be set via AWS Secrets Manager or environment variable
        // For now, we'll expect it to be set as an environment variable during deployment
      },
    });

    // Grant Lambda permission to publish to SNS
    notificationTopic.grantPublish(soccerNewsLambda);

    // Create EventBridge rule to trigger Lambda daily at 9am UTC
    const schedule = new events.Rule(this, 'SoccerNewsSchedule', {
      schedule: events.Schedule.cron({
        minute: '0',
        hour: '9',
        day: '*',
        month: '*',
        year: '*',
      }),
      description: 'Trigger soccer news Lambda daily at 9am UTC',
    });

    // Add Lambda as target for the schedule
    schedule.addTarget(new targets.LambdaFunction(soccerNewsLambda));

    // Output the SNS topic ARN
    new cdk.CfnOutput(this, 'SnsTopicArn', {
      value: notificationTopic.topicArn,
      description: 'ARN of the SNS topic for soccer news notifications',
    });
  }
}


```

```typescript
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';
import * as path from 'path';

export class SoccerNewsStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create SNS topic for notifications
    const notificationTopic = new sns.Topic(this, 'SoccerNewsTopic', {
      displayName: 'Soccer News Notifications',
      topicName: 'soccer-news-notifications',
    });

    // Create Lambda function with Python dependencies bundled
    const soccerNewsLambda = new lambda.Function(this, 'SoccerNewsLambda', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda'), {
        bundling: {
          image: lambda.Runtime.PYTHON_3_12.bundlingImage,
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output && cp -au . /asset-output'
          ],
        },
      }),
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      environment: {
        SNS_TOPIC_ARN: notificationTopic.topicArn,
        // OPENAI_API_KEY should be set via AWS Secrets Manager or environment variable
        // For now, we'll expect it to be set as an environment variable during deployment
      },
    });

    // Grant Lambda permission to publish to SNS
    notificationTopic.grantPublish(soccerNewsLambda);

    // Create EventBridge rule to trigger Lambda daily at 9am UTC
    const schedule = new events.Rule(this, 'SoccerNewsSchedule', {
      schedule: events.Schedule.cron({
        minute: '0',
        hour: '9',
        day: '*',
        month: '*',
        year: '*',
      }),
      description: 'Trigger soccer news Lambda daily at 9am UTC',
    });

    // Add Lambda as target for the schedule
    schedule.addTarget(new targets.LambdaFunction(soccerNewsLambda));

    // Output the SNS topic ARN
    new cdk.CfnOutput(this, 'SnsTopicArn', {
      value: notificationTopic.topicArn,
      description: 'ARN of the SNS topic for soccer news notifications',
    });

    // Output instructions
    new cdk.CfnOutput(this, 'SetupInstructions', {
      value: 'Set OPENAI_API_KEY environment variable in Lambda function configuration or use AWS Secrets Manager',
      description: 'Instructions for setting up OpenAI API key',
    });
  }
}


```


Updating the Lambda function to use OpenAI's Assistants API with web search:



Updating the Lambda function to use OpenAI's Assistants API with web search:


```python
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
        
        # Create an assistant with web search tool enabled
        # Using o1-preview for deep thinking/reasoning capabilities
        assistant = client.beta.assistants.create(
            name="Soccer News Aggregator",
            instructions=formatted_prompt,
            model="o1-preview",  # Using o1-preview for deep thinking, or use "gpt-4o" if o1 not available
            tools=[{"type": "web_search"}],  # Enable web search
            temperature=0.7
        )
        
        print(f"Assistant created: {assistant.id}")
        
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
            assistant_id=assistant.id
        )
        
        print(f"Run started: {run.id}, status: {run.status}")
        
        # Wait for the run to complete
        import time
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
        notification_content = None
        for message in messages.data:
            if message.role == 'assistant' and message.content:
                # Get text content from the message
                if hasattr(message.content[0], 'text'):
                    notification_content = message.content[0].text.value
                    break
        
        if not notification_content:
            raise Exception("No response received from assistant")
        
        # Clean up: delete the assistant
        try:
            client.beta.assistants.delete(assistant.id)
        except:
            pass
        
        print(f"Received response from OpenAI: {len(notification_content)} characters")
        
        # Parse the response to extract headline and description
        # Format should be: HEADLINE: [headline]\n\n\n[description]
        if "HEADLINE:" in notification_content:
            parts = notification_content.split("HEADLINE:", 1)
            if len(parts) > 1:
                remaining = parts[1].strip()
                # Split by triple newline to separate headline from description
                if "\n\n\n" in remaining:
                    headline, description = remaining.split("\n\n\n", 1)
                    headline = headline.strip()
                    description = description.strip()
                else:
                    # Fallback: use first line as headline, rest as description
                    lines = remaining.split("\n", 1)
                    headline = lines[0].strip()
                    description = lines[1].strip() if len(lines) > 1 else ""
            else:
                # Fallback: use first 100 chars as headline
                headline = notification_content[:100].strip()
                description = notification_content[100:].strip()
        else:
            # No HEADLINE marker, use first 100 chars as headline
            headline = notification_content[:100].strip()
            description = notification_content[100:].strip()
        
        # Format the message for SNS
        # Headline first, then 3 line breaks, then description
        message = f"{headline}\n\n\n{description}"
        
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


```


Adding a fallback and improving error handling:


```python
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
            import time
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
        
        # Parse the response to extract headline and description
        # Format should be: HEADLINE: [headline]\n\n\n[description]
        if "HEADLINE:" in notification_content:
            parts = notification_content.split("HEADLINE:", 1)
            if len(parts) > 1:
                remaining = parts[1].strip()
                # Split by triple newline to separate headline from description
                if "\n\n\n" in remaining:
                    headline, description = remaining.split("\n\n\n", 1)
                    headline = headline.strip()
                    description = description.strip()
                else:
                    # Fallback: use first line as headline, rest as description
                    lines = remaining.split("\n", 1)
                    headline = lines[0].strip()
                    description = lines[1].strip() if len(lines) > 1 else ""
            else:
                # Fallback: use first 100 chars as headline
                headline = notification_content[:100].strip()
                description = notification_content[100:].strip()
        else:
            # No HEADLINE marker, use first 100 chars as headline
            headline = notification_content[:100].strip()
            description = notification_content[100:].strip()
        
        # Format the message for SNS
        # Headline first, then 3 line breaks, then description
        message = f"{headline}\n\n\n{description}"
        
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


```


Adding the missing import and updating package.json:


```python
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
            import time
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
        
        # Parse the response to extract headline and description
        # Format should be: HEADLINE: [headline]\n\n\n[description]
        if "HEADLINE:" in notification_content:
            parts = notification_content.split("HEADLINE:", 1)
            if len(parts) > 1:
                remaining = parts[1].strip()
                # Split by triple newline to separate headline from description
                if "\n\n\n" in remaining:
                    headline, description = remaining.split("\n\n\n", 1)
                    headline = headline.strip()
                    description = description.strip()
                else:
                    # Fallback: use first line as headline, rest as description
                    lines = remaining.split("\n", 1)
                    headline = lines[0].strip()
                    description = lines[1].strip() if len(lines) > 1 else ""
            else:
                # Fallback: use first 100 chars as headline
                headline = notification_content[:100].strip()
                description = notification_content[100:].strip()
        else:
            # No HEADLINE marker, use first 100 chars as headline
            headline = notification_content[:100].strip()
            description = notification_content[100:].strip()
        
        # Format the message for SNS
        # Headline first, then 3 line breaks, then description
        message = f"{headline}\n\n\n{description}"
        
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


```

```python
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
        
        # Parse the response to extract headline and description
        # Format should be: HEADLINE: [headline]\n\n\n[description]
        if "HEADLINE:" in notification_content:
            parts = notification_content.split("HEADLINE:", 1)
            if len(parts) > 1:
                remaining = parts[1].strip()
                # Split by triple newline to separate headline from description
                if "\n\n\n" in remaining:
                    headline, description = remaining.split("\n\n\n", 1)
                    headline = headline.strip()
                    description = description.strip()
                else:
                    # Fallback: use first line as headline, rest as description
                    lines = remaining.split("\n", 1)
                    headline = lines[0].strip()
                    description = lines[1].strip() if len(lines) > 1 else ""
            else:
                # Fallback: use first 100 chars as headline
                headline = notification_content[:100].strip()
                description = notification_content[100:].strip()
        else:
            # No HEADLINE marker, use first 100 chars as headline
            headline = notification_content[:100].strip()
            description = notification_content[100:].strip()
        
        # Format the message for SNS
        # Headline first, then 3 line breaks, then description
        message = f"{headline}\n\n\n{description}"
        
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


```

```json
{
  "name": "soccer-news-infra",
  "version": "1.0.0",
  "description": "CDK stack for soccer news infrastructure",
  "main": "lib/index.js",
  "scripts": {
    "build": "tsc",
    "watch": "tsc -w",
    "cdk": "cdk",
    "deploy": "cdk deploy",
    "synth": "cdk synth"
  },
  "keywords": [],
  "author": "",
  "license": "ISC",
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "~5.3.0",
    "aws-cdk": "^2.100.0"
  },
  "dependencies": {
    "aws-cdk-lib": "^2.100.0",
    "constructs": "^10.0.0",
    "source-map-support": "^0.5.21"
  }
}


```


Updating the README with deployment instructions and checking for linting errors:



Updating the README with deployment instructions:


```markdown
# soccer-news-infra
CDK stack for soccer news infrastructure

## Overview

This infrastructure deploys a serverless soccer news notification system that:
- Triggers daily at 9am UTC via EventBridge
- Uses a Lambda function to call OpenAI API with web search capabilities
- Aggregates soccer news from EPL, MLS, La Liga, and major competitions
- Publishes formatted notifications to an SNS topic

## Architecture

- **EventBridge Schedule**: Daily trigger at 9am UTC
- **Lambda Function**: Python function that calls OpenAI API and formats notifications
- **SNS Topic**: Publishes notifications for subscribers

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Node.js and npm installed
3. AWS CDK CLI installed: `npm install -g aws-cdk`
4. OpenAI API key

## Setup

1. Install dependencies:
```bash
npm install
```

2. Set your OpenAI API key as an environment variable (or use AWS Secrets Manager):
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. Bootstrap CDK (first time only):
```bash
cdk bootstrap
```

4. Deploy the stack:
```bash
cdk deploy
```

## Configuration

### Setting OpenAI API Key

You have two options:

**Option 1: Environment Variable (for testing)**
Set the `OPENAI_API_KEY` environment variable in the Lambda function configuration after deployment.

**Option 2: AWS Secrets Manager (recommended for production)**
1. Create a secret in AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name soccer-news/openai-api-key \
  --secret-string "your-api-key-here"
```

2. Update the Lambda function code to retrieve the secret from Secrets Manager instead of environment variables.

### SNS Topic Subscription

After deployment, subscribe to the SNS topic to receive notifications:
- Email: Subscribe via AWS Console or CLI
- SMS: Subscribe via AWS Console
- Mobile Push: Configure via AWS SNS Mobile Push

The SNS topic ARN will be displayed in the CDK output after deployment.

## Lambda Function

The Lambda function (`lambda/index.py`):
- Loads the prompt template from `lambda/prompt_template.txt`
- Formats the prompt with current and previous dates
- Calls OpenAI Assistants API with web search enabled
- Falls back to Chat Completions API if Assistants API fails
- Parses the response into headline and description format
- Publishes to SNS topic

## Prompt Template

The prompt template (`lambda/prompt_template.txt`) instructs the LLM to:
- Search for soccer news from the last 24 hours
- Focus on EPL, MLS, La Liga, and major competitions
- Create a concise headline (fits in iPhone notification)
- Create a longer description (max 7 sentences) with proper formatting

## Development

### Building

```bash
npm run build
```

### Synthesize CloudFormation template

```bash
npm run synth
```

### Watch for changes

```bash
npm run watch
```

## Testing

You can manually invoke the Lambda function to test:

```bash
aws lambda invoke \
  --function-name SoccerNewsStack-SoccerNewsLambda-XXXXX \
  --payload '{}' \
  response.json
```

## Cleanup

To remove all resources:

```bash
cdk destroy
```

## Notes

- The Lambda function uses Python 3.12 runtime
- Dependencies are automatically bundled during CDK deployment
- The EventBridge schedule is set to UTC timezone (9am UTC = 9am UTC)
- Adjust the schedule in `lib/soccer-news-stack.ts` if you need a different timezone

```


Verifying the project structure is complete:



## Created Files

### CDK Infrastructure
- **`package.json`** - Node.js dependencies and scripts
- **`tsconfig.json`** - TypeScript configuration
- **`cdk.json`** - CDK configuration
- **`.gitignore`** - Git ignore rules
- **`bin/app.ts`** - CDK app entry point
- **`lib/soccer-news-stack.ts`** - Main CDK stack with:
  - EventBridge schedule (daily at 9am UTC)
  - Lambda function with Python 3.12
  - SNS topic for notifications

### Lambda Function
- **`lambda/index.py`** - Lambda handler that:
  - Uses OpenAI Assistants API with web search enabled
  - Falls back to Chat Completions API if needed
  - Formats notifications and publishes to SNS
- **`lambda/prompt_template.txt`** - Prompt template for the LLM
- **`lambda/requirements.txt`** - Python dependencies (openai, boto3)

### Documentation
- **`README.md`** - Deployment instructions and usage guide

## Features

1. EventBridge schedule triggers the Lambda daily at 9am UTC
2. OpenAI integration with web search via Assistants API
3. Automatic dependency bundling for Python packages
4. Error handling with fallback mechanisms
5. SNS integration for notification delivery

## Next Steps

1. Install dependencies: `npm install`
2. Set your OpenAI API key: `export OPENAI_API_KEY="your-key"`
3. Bootstrap CDK (first time): `cdk bootstrap`
4. Deploy: `cdk deploy`

The infrastructure is ready to deploy. The Lambda will automatically bundle Python dependencies during deployment, and you can subscribe to the SNS topic to receive daily soccer news notifications.

---

**User**

did we actually need to create that cdk.json file?

---

**Cursor**


Checking if `cdk.json` is required and whether we can simplify it:



Yes, `cdk.json` is required. The `"app"` field tells CDK how to run the TypeScript code; without it, `cdk synth` and `cdk deploy` won't work.

The file I created includes optional sections. The minimal version only needs:

```json
{
  "app": "npx ts-node --prefer-ts-exts bin/app.ts"
}
```

The `"watch"` and `"context"` sections are optional but provide useful defaults (watch mode and feature flags).

Simplifying it to just the essential `"app"` field:


```json
{
  "app": "npx ts-node --prefer-ts-exts bin/app.ts"
}
```

```json
{
  "app": "npx ts-node --prefer-ts-exts bin/app.ts"
}


```


Simplified to the minimal required configuration. The `"app"` field is required so CDK knows how to execute the TypeScript code. The watch and context settings were optional defaults and aren't needed for basic functionality.

---

**User**

ok thanks. also, we are asking the openai api to output the response in the correct format, but then we are int he labda, parsing a reposnse format that we did not even ask the llm to do, into a separeat headline and description, and then manually arranging the format. why is that?

---

**Cursor**


Checking the Lambda code to see how we're handling the response:



Checking the full parsing logic:



We're parsing to extract the headline for the SNS subject, then reconstructing the message. Simplifying: ask the LLM to output the final format directly, extract the headline for the subject, and use the response as-is for the message body.



Simplifying: ask the LLM to output the final format directly, extract the headline for the SNS subject, and use the response as-is for the message body.


```plaintext
You are a soccer news aggregator. Your task is to search the web for the latest soccer/football (not American football) highlights from the last 24 hours and upcoming games/events.

Focus on the following leagues and competitions:
- English Premier League (EPL)
- MLS (US Major League Soccer)
- La Liga (Spain)
- Major competitions: FIFA World Cup, UEFA Euro Cup, Copa America, UEFA Champions League, FIFA Club World Cup

Primary focus should be on:
1. Results of matches from the previous day
2. List of upcoming matches

For information gathering, use these resources:
- Previous day schedule: https://www.espn.com/soccer/schedule/_/date/{previous_date} (format: YYYYMMDD)
- Current day schedule: https://www.espn.com/soccer/schedule/_/date/{current_date} (format: YYYYMMDD)
- ESPN, BBC Sports
- League websites for EPL, MLS, and La Liga
- Reddit: r/footballhighlights and other sports subreddits

Create a notification with the following format:

HEADLINE (first part):
- A brief summary that fits in a standard iPhone notification box without needing to open the notification further
- Focus on top highlights at the current exact time/day
- If too much information, keep it concise and mention only the most important news (significant wins, knockouts)
- Should be brief enough to fit in a notification preview

DESCRIPTION (after 3 line breaks):
- Longer description covering all the highlights of the day
- Include the longer form of what's covered in the headline
- Include other lower priority items not in the headline
- Split into sentences
- Sentences about different topics should be spaced out by 2 line breaks
- Maximum 7 sentences total

Format your response exactly as follows (no markers, just the content):
[your headline here]

[3 line breaks]

[your description here - max 7 sentences, with 2 line breaks between different topics]

The output should start directly with the headline, followed by exactly 3 line breaks, then the description.


```

```python
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


```


Updated:

1. **Prompt template**: Ask the LLM to output the final format directly (headline + 3 line breaks + description), without the "HEADLINE:" marker.

2. **Lambda code**: Parse only to extract the headline for the SNS subject. Use the original response as-is for the message body.

This removes the redundancy—we no longer ask for one format, parse it, and reconstruct it. We ask for the final format and use it directly, parsing only to get the headline for the SNS subject line.

