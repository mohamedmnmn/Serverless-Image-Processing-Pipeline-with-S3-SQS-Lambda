# Architecture Notes

## Request path

The upload request is split into two operations:

1. API Gateway invokes an upload-URL Lambda.
2. The client uploads the image directly to S3 using a short-lived pre-signed URL.

This keeps large image payloads away from API Gateway and Lambda.

## Event path

The source S3 bucket emits object-created notifications to SQS. The queue is the durability boundary between ingestion and processing.

The SQS event source mapping invokes the queue-consumer Lambda. The consumer validates the message and starts a Step Functions Standard execution.

## Processing path

Step Functions coordinates the processing stages. Image transformation code runs in Lambda with Pillow supplied by a compatible Lambda Layer or container image.

The destination bucket is different from the source bucket, preventing processed objects from triggering the source notification path.

## Delivery path

CloudFront reads the destination bucket through Origin Access Control. Users receive processed images through CloudFront instead of direct public S3 access.

## Failure path

Transient failures are retried. Messages that repeatedly fail SQS processing are moved to the DLQ. Step Functions catches terminal workflow errors, records FAILED status in DynamoDB, and publishes an SNS notification.

## Security boundaries

- Source and destination buckets remain private.
- API Gateway exposes only the upload URL operation.
- S3 access is granted to specific IAM roles.
- CloudFront is allowed to read only the destination content required for delivery.
- No AWS credentials are embedded in Lambda code.
