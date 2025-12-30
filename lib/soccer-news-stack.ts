import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as sns from "aws-cdk-lib/aws-sns";
import * as iam from "aws-cdk-lib/aws-iam";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import { Construct } from "constructs";
import * as path from "path";

export class SoccerNewsStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        // Create SNS topic for notifications
        const notificationTopic = new sns.Topic(this, "SoccerNewsTopic", {
            displayName: "Soccer News Notifications",
            topicName: "soccer-news-notifications",
        });

        // Create or reference the secret for OpenAI API key
        // If the secret doesn't exist, it will need to be created manually:
        // aws secretsmanager create-secret --name soccer-news/openai-api-key --secret-string "your-api-key"
        const openaiApiKeySecret = secretsmanager.Secret.fromSecretNameV2(
            this,
            "OpenAIApiKeySecret",
            "soccer-news/openai-api-key"
        );

        // Create Lambda function with Python dependencies bundled
        const soccerNewsLambda = new lambda.Function(this, "SoccerNewsLambda", {
            runtime: lambda.Runtime.PYTHON_3_12,
            handler: "index.handler",
            code: lambda.Code.fromAsset(path.join(__dirname, "../lambda"), {
                bundling: {
                    image: lambda.Runtime.PYTHON_3_12.bundlingImage,
                    command: [
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                },
            }),
            timeout: cdk.Duration.minutes(5),
            memorySize: 512,
            environment: {
                SNS_TOPIC_ARN: notificationTopic.topicArn,
                OPENAI_SECRET_NAME: openaiApiKeySecret.secretName,
            },
        });

        // Grant Lambda permission to read the secret
        openaiApiKeySecret.grantRead(soccerNewsLambda);

        // Grant Lambda permission to publish to SNS
        notificationTopic.grantPublish(soccerNewsLambda);

        // Create EventBridge rule to trigger Lambda daily at 9am UTC
        const schedule = new events.Rule(this, "SoccerNewsSchedule", {
            schedule: events.Schedule.cron({
                minute: "0",
                hour: "9",
                day: "*",
                month: "*",
                year: "*",
            }),
            description: "Trigger soccer news Lambda daily at 9am UTC",
        });

        // Add Lambda as target for the schedule
        schedule.addTarget(new targets.LambdaFunction(soccerNewsLambda));

        // Output the SNS topic ARN
        new cdk.CfnOutput(this, "SnsTopicArn", {
            value: notificationTopic.topicArn,
            description: "ARN of the SNS topic for soccer news notifications",
        });

        // Output instructions
        new cdk.CfnOutput(this, "SetupInstructions", {
            value: `Create the secret 'soccer-news/openai-api-key' in AWS Secrets Manager with your OpenAI API key. Run: aws secretsmanager create-secret --name soccer-news/openai-api-key --secret-string "your-api-key"`,
            description: "Instructions for setting up OpenAI API key",
        });
    }
}
