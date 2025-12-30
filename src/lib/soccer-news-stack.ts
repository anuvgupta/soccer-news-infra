import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as sns from "aws-cdk-lib/aws-sns";
import * as iam from "aws-cdk-lib/aws-iam";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import { Construct } from "constructs";
import * as path from "path";
import * as fs from "fs";

interface SoccerNewsStackProps extends cdk.StackProps {
    stageName: string;
    openaiApiKey: string;
}

export class SoccerNewsStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: SoccerNewsStackProps) {
        super(scope, id, props);

        // Create SNS topic for notifications
        const notificationTopic = new sns.Topic(this, "SoccerNewsTopic", {
            displayName: "Soccer News Notifications",
            topicName: `soccer-news-notifications-${this.account}-${props.stageName}`,
        });

        // Create Lambda function with Python dependencies bundled
        // Using local bundling to avoid Docker requirement
        const lambdaCode = lambda.Code.fromAsset(
            path.join(__dirname, "../lambda"),
            {
                bundling: {
                    image: lambda.Runtime.PYTHON_3_12.bundlingImage,
                    command: [
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                    ],
                    // Try local bundling first, fall back to Docker if available
                    local: {
                        tryBundle(outputDir: string): boolean {
                            try {
                                const { execSync } = require("child_process");
                                const lambdaDir = path.join(
                                    __dirname,
                                    "../lambda"
                                );

                                // Check if Python 3.12 is available
                                try {
                                    execSync("python3.12 --version", {
                                        stdio: "ignore",
                                    });
                                } catch {
                                    // Try python3 as fallback
                                    try {
                                        execSync("python3 --version", {
                                            stdio: "ignore",
                                        });
                                    } catch {
                                        console.warn(
                                            "Python 3 not found, falling back to Docker bundling"
                                        );
                                        return false;
                                    }
                                }

                                // Install dependencies locally
                                console.log(
                                    "Installing Python dependencies locally..."
                                );
                                execSync(
                                    `pip3 install -r ${path.join(
                                        lambdaDir,
                                        "requirements.txt"
                                    )} -t ${outputDir}`,
                                    {
                                        stdio: "inherit",
                                        cwd: lambdaDir,
                                    }
                                );

                                // Copy Lambda code files (excluding dependencies which are already installed)
                                const filesToCopy = [
                                    "index.py",
                                    "prompt_template.txt",
                                ];
                                for (const file of filesToCopy) {
                                    const src = path.join(lambdaDir, file);
                                    const dest = path.join(outputDir, file);
                                    if (fs.existsSync(src)) {
                                        fs.copyFileSync(src, dest);
                                    }
                                }

                                return true;
                            } catch (error) {
                                console.warn(
                                    "Local bundling failed, will use Docker:",
                                    error
                                );
                                return false;
                            }
                        },
                    },
                },
            }
        );

        const soccerNewsLambda = new lambda.Function(this, "SoccerNewsLambda", {
            runtime: lambda.Runtime.PYTHON_3_12,
            handler: "index.handler",
            code: lambdaCode,
            timeout: cdk.Duration.minutes(5),
            memorySize: 512,
            environment: {
                SNS_TOPIC_ARN: notificationTopic.topicArn,
                OPENAI_API_KEY: props.openaiApiKey,
            },
        });

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

        // // Add Lambda as target for the schedule
        // schedule.addTarget(new targets.LambdaFunction(soccerNewsLambda));

        // Output the SNS topic ARN
        new cdk.CfnOutput(this, "SnsTopicArn", {
            value: notificationTopic.topicArn,
            description: "ARN of the SNS topic for soccer news notifications",
        });
    }
}
