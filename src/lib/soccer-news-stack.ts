import * as cdk from "aws-cdk-lib";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import { Construct } from "constructs";
import * as path from "path";

interface SoccerNewsStackProps extends cdk.StackProps {
    stageName: string;
    openaiApiKey: string;
}

export class SoccerNewsStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: SoccerNewsStackProps) {
        super(scope, id, props);

        // Browser Lambda for headless browsing
        const browserLambda = new lambda.DockerImageFunction(
            this,
            "BrowserLambda",
            {
                code: lambda.DockerImageCode.fromImageAsset(
                    path.join(__dirname, "../lambdas/browser"),
                    {
                        platform: cdk.aws_ecr_assets.Platform.LINUX_AMD64,
                    }
                ),
                timeout: cdk.Duration.minutes(2),
                memorySize: 3008,
                architecture: lambda.Architecture.X86_64,
                description: "Headless browser Lambda for web scraping",
            }
        );

        // Main job Lambda for soccer news aggregation
        const jobLambda = new lambda.DockerImageFunction(this, "JobLambda", {
            code: lambda.DockerImageCode.fromImageAsset(
                path.join(__dirname, "../lambdas/job"),
                {
                    platform: cdk.aws_ecr_assets.Platform.LINUX_AMD64,
                }
            ),
            timeout: cdk.Duration.minutes(10),
            memorySize: 2048,
            architecture: lambda.Architecture.X86_64,
            environment: {
                OPENAI_API_KEY: props.openaiApiKey,
                BROWSER_LAMBDA_ARN: browserLambda.functionArn,
            },
        });

        // Grant Job Lambda permission to invoke Browser Lambda
        browserLambda.grantInvoke(jobLambda);

        // Create EventBridge rule to trigger Lambda daily at 9am UTC (commented out for now)
        // const schedule = new events.Rule(this, "SoccerNewsSchedule", {
        //     schedule: events.Schedule.cron({
        //         minute: "0",
        //         hour: "9",
        //         day: "*",
        //         month: "*",
        //         year: "*",
        //     }),
        //     description: "Trigger soccer news Lambda daily at 9am UTC",
        // });

        // // Add Lambda as target for the schedule
        // schedule.addTarget(new targets.LambdaFunction(jobLambda));

        // Output the Lambda function names for easy testing
        new cdk.CfnOutput(this, "JobLambdaFunctionName", {
            value: jobLambda.functionName,
            description: "Name of the Job Lambda function",
        });

        new cdk.CfnOutput(this, "BrowserLambdaFunctionName", {
            value: browserLambda.functionName,
            description: "Name of the Browser Lambda function",
        });

        new cdk.CfnOutput(this, "BrowserLambdaArn", {
            value: browserLambda.functionArn,
            description: "ARN of the Browser Lambda function",
        });
    }
}
