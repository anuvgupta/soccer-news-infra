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

        const lambdaCode = lambda.Code.fromAsset(
            path.join(__dirname, "../lambda"),
            {
                bundling: {
                    image: lambda.Runtime.PYTHON_3_12.bundlingImage,
                    command: [
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output --platform manylinux2014_x86_64 --only-binary=:all: --no-cache-dir && cp -au . /asset-output",
                    ],
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
                OPENAI_API_KEY: props.openaiApiKey,
            },
        });

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
        // schedule.addTarget(new targets.LambdaFunction(soccerNewsLambda));

        // Output the Lambda function name for easy testing
        new cdk.CfnOutput(this, "LambdaFunctionName", {
            value: soccerNewsLambda.functionName,
            description: "Name of the Lambda function",
        });
    }
}
