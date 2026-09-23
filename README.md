# Serverless Image Processing Pipeline with S3, SQS & Lambda

**Serverless Image Processing Pipeline with S3, SQS & Lambda** is a reference architecture for asynchronously processing uploaded images using AWS managed services. It demonstrates reliable event-driven processing with Amazon S3, Amazon SQS, AWS Lambda, AWS Step Functions, Amazon DynamoDB, Amazon SNS, and Amazon CloudFront.

## Table of Content

- [Solution Overview](#solution-overview)
- [Architecture Diagram](#architecture-diagram)
- [AWS Services](#aws-services)
- [How the Solution Works](#how-the-solution-works)
- [Reliability and Failure Handling](#reliability-and-failure-handling)
- [Security](#security)
- [Customization](#customization)
  - [Prerequisites](#prerequisites)
  - [1. Clone the repository](#1-clone-the-repository)
  - [2. Install Dependencies and Test](#2-install-dependencies-and-test)
  - [3. Deploy](#3-deploy)
- [Repository Structure](#repository-structure)
- [Cost Considerations](#cost-considerations)
- [Learning Outcomes](#learning-outcomes)
- [License](#license)

# Solution Overview

This project implements a serverless image-processing pipeline designed to separate image ingestion from processing.

A client first requests a short-lived pre-signed upload URL through **Amazon API Gateway** and **AWS Lambda**. The client then uploads the original image directly to an **Amazon S3 source bucket**.

When the upload completes, an S3 event is sent to an **Amazon SQS processing queue**. SQS provides buffering, retry behavior, and a dead-letter queue for messages that cannot be processed successfully.

An SQS-triggered Lambda validates the event and starts an **AWS Step Functions Standard workflow**. The workflow coordinates image validation, resizing, watermarking, storing the processed images, updating **Amazon DynamoDB**, and publishing an **Amazon SNS** notification.

Processed images are stored in a separate S3 destination bucket and delivered to users through **Amazon CloudFront**. The destination bucket remains private and is accessed by CloudFront using Origin Access Control.

# Architecture Diagram

![Serverless Image Processing Pipeline Architecture](./architecture.svg)

### Architecture flow

```text
Client
  |
  v
API Gateway
  |
  v
Lambda - Pre-signed URL
  |
  v
S3 Source Bucket
  |
  | Object Created
  v
SQS Processing Queue -----> SQS DLQ
  |
  v
Lambda Queue Consumer
  |
  v
Step Functions Standard
  |
  +--> Validate
  |
  +--> Resize + Watermark (Lambda + Pillow)
  |
  +--> Store processed images
  |
  +--> DynamoDB metadata/status
  |
  +--> SNS success/failure
  |
  v
S3 Destination Bucket
  |
  v
CloudFront
  |
  v
Users
```

# AWS Services

| AWS Service | Purpose |
|---|---|
| Amazon S3 | Stores original and processed images |
| Amazon API Gateway | Provides the upload URL API |
| AWS Lambda | Generates upload URLs, consumes SQS events, and processes images |
| Amazon SQS | Buffers image events and decouples ingestion from processing |
| Amazon SQS DLQ | Stores messages that repeatedly fail processing |
| AWS Step Functions | Orchestrates the multi-step processing workflow |
| Amazon DynamoDB | Stores image metadata and processing status |
| Amazon SNS | Sends completion and failure notifications |
| Amazon CloudFront | Provides global, cached delivery of processed images |
| Amazon CloudWatch | Provides logs, metrics, and operational monitoring |

# How the Solution Works

## 1. Generate upload URL

The client sends:

```text
POST /upload-url
```

The API invokes Lambda, which creates a short-lived pre-signed S3 PUT URL.

The client uploads directly to S3 rather than sending the image through API Gateway.

## 2. S3 event notification

After the upload, the source S3 bucket publishes an object-created notification to the SQS processing queue.

The source and destination buckets are separate so generated images do not re-enter the source processing path.

## 3. SQS buffering

SQS provides a durable buffer between image uploads and image processing.

This allows upload traffic to temporarily exceed processing capacity without requiring the processing layer to scale at exactly the same rate.

A DLQ is configured for messages that exceed the allowed receive/retry count.

## 4. Lambda queue consumer

Lambda consumes messages from SQS.

The consumer validates the S3 event, extracts the bucket/key information, creates a deterministic image/job ID, and starts the Step Functions workflow.

## 5. Step Functions workflow

The Standard workflow coordinates:

1. Validate the image event.
2. Read the source image.
3. Resize the image.
4. Apply a watermark.
5. Create thumbnail and full-size derivatives.
6. Store derivatives in the destination S3 bucket.
7. Write metadata and status to DynamoDB.
8. Publish an SNS completion event.

Failures are caught and reported through the failure path.

## 6. Image processing

The example Lambda processor uses **Pillow**.

It creates:

```text
processed/{image-id}/thumbnail.jpg
processed/{image-id}/full.jpg
```

For deployment, Pillow should be supplied using a Lambda Layer or a Lambda container image compatible with the selected runtime and architecture.

## 7. Global delivery

CloudFront uses the private destination S3 bucket as its origin.

Users access processed images through CloudFront rather than public S3 object URLs.

# Reliability and Failure Handling

### SQS

- Standard SQS queue
- Visibility timeout greater than the Lambda timeout
- Bounded retry count
- Dead-letter queue
- Lambda event source mapping
- Optional reserved concurrency to protect downstream resources

### Step Functions

Transient Lambda failures should use retry policies with exponential backoff.

Terminal failures should be caught so that the job can be marked FAILED in DynamoDB and an SNS failure notification can be published.

### Idempotency

S3 notifications can be delivered more than once. Processing should therefore use deterministic job/image identifiers and idempotent writes.

# Security

The reference architecture follows these security principles:

- Source and destination S3 buckets are private.
- CloudFront uses Origin Access Control for S3 access.
- S3 bucket policies deny unnecessary public access.
- Lambda and Step Functions use least-privilege IAM roles.
- Uploads use short-lived pre-signed URLs.
- API Gateway and CloudFront use HTTPS.
- Data at rest can be encrypted with AWS-managed or customer-managed KMS keys.
- No AWS credentials are stored in source code.
- Secrets, if required, should be stored in AWS Secrets Manager.

# Customization

The repository is structured similarly to an AWS Solutions reference project: documentation and architecture at the repository root, deployment material under deployment/, and application/source material under source/.

## Prerequisites

For the example source code:

- AWS account
- AWS CLI
- Python 3.12+ for local development
- Appropriate AWS IAM permissions
- Pillow for local image-processing tests

For infrastructure deployment, use an infrastructure-as-code tool such as AWS SAM, AWS CDK, or Terraform.

## 1. Clone the repository

```bash
git clone https://github.com/mohamedmnmn/Serverless-Image-Processing-Pipeline-with-S3-SQS-Lambda.git
cd Serverless-Image-Processing-Pipeline-with-S3-SQS-Lambda
```

## 2. Install Dependencies and Test

```bash
cd source/image_processor
python -m pip install -r requirements.txt
```

The image processor can then be packaged for Lambda using a compatible Lambda Layer or container image.

Before deployment, validate the Lambda code and test the processing logic with representative JPEG/PNG files.

## 3. Deploy

The AWS resources should be provisioned using infrastructure as code.

A deployment must create and configure, at minimum:

- source S3 bucket
- destination S3 bucket
- S3 event notification
- SQS queue
- SQS DLQ and redrive policy
- SQS-to-Lambda event source mapping
- queue-consumer Lambda
- Step Functions Standard state machine
- image-processing Lambda and Pillow dependency
- DynamoDB table
- SNS topic
- API Gateway upload endpoint
- upload URL Lambda
- CloudFront distribution with S3 Origin Access Control
- IAM roles and policies
- CloudWatch logging/monitoring
- S3 lifecycle configuration

Environment-specific values such as bucket names, AWS Region, CloudFront distribution settings, DynamoDB table name, and SNS topic ARN should not be hard-coded.

**Important:** Never commit AWS access keys, secret keys, private keys, or other credentials to this repository.

# Repository Structure

```text
.
├── README.md
├── architecture.svg
├── .gitignore
├── deployment/
│   └── README.md
├── docs/
│   ├── architecture-notes.md
│   └── architecture.svg
└── source/
    ├── README.md
    └── image_processor/
        ├── app.py
        └── requirements.txt
```

# Cost Considerations

The architecture uses serverless, usage-based AWS services. Costs can come from:

- S3 storage and requests
- SQS requests
- Lambda execution
- Step Functions state transitions
- DynamoDB capacity/storage
- SNS messages
- CloudFront requests and data transfer
- CloudWatch logs

For development and student testing, delete unused resources after testing and configure appropriate S3 lifecycle rules.

# Learning Outcomes

This project demonstrates:

- Event-driven architecture with S3 and SQS
- Reliable asynchronous processing
- SQS retries and dead-letter queues
- Lambda image processing
- Lambda dependency packaging with Pillow
- Step Functions workflow orchestration
- S3 lifecycle management
- DynamoDB metadata persistence
- SNS completion/failure notifications
- CloudFront global image delivery
- Private S3 origins with CloudFront OAC
- Least-privilege IAM

# License

This project is provided as an educational reference implementation for an AWS serverless architecture project.