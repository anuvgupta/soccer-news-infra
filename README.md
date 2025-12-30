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

The Lambda function is configured to retrieve the OpenAI API key from AWS Secrets Manager by default.

**Create the secret before deploying (or after, but before the first run):**
```bash
aws secretsmanager create-secret \
  --name soccer-news/openai-api-key \
  --secret-string "your-api-key-here"
```

The Lambda function has been granted permission to read this secret automatically.

**Note:** For local testing, you can set the `OPENAI_API_KEY` environment variable, and the Lambda will use it if the secret name is not configured. However, in the deployed environment, Secrets Manager is the recommended approach.

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
