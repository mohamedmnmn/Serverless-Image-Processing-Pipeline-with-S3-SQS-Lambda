# Deployment

This directory is reserved for infrastructure-as-code and deployment automation.

## Required resources

A complete deployment should provision:

- S3 source bucket
- S3 destination bucket
- SQS processing queue
- SQS dead-letter queue
- S3 event notification to SQS
- Lambda queue consumer
- Step Functions Standard state machine
- Lambda image processor
- Pillow Lambda Layer or container image
- DynamoDB ImageJobs table
- SNS notification topic
- API Gateway upload URL endpoint
- Lambda pre-signed URL generator
- CloudFront distribution
- CloudFront Origin Access Control
- IAM roles and least-privilege policies
- CloudWatch log groups and alarms
- S3 lifecycle rules

## Infrastructure-as-code

AWS SAM, AWS CDK, or Terraform can be used to implement these resources.

The README at the repository root documents the architecture and deployment requirements. Environment-specific values and credentials must never be committed.
