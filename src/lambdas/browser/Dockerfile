# Use AWS Lambda Node.js 20 base image
FROM public.ecr.aws/lambda/nodejs:20

# Copy package files
COPY package*.json ${LAMBDA_TASK_ROOT}/

# Install dependencies directly in the Lambda environment
RUN npm ci --omit=dev

# Copy Lambda function code
COPY index.mjs ${LAMBDA_TASK_ROOT}/

# Set the Lambda handler
CMD [ "index.handler" ]

