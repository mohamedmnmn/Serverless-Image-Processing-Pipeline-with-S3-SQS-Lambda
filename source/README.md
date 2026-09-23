# Source

This directory contains the application code used by the image-processing pipeline.

## Components

- image processor Lambda
- Pillow dependency definition
- application-specific processing logic

The Lambda reads an image from the source S3 bucket, creates a thumbnail and full-size derivative, applies a watermark, and writes the results to the destination S3 bucket.

For AWS deployment, package Pillow as a compatible Lambda Layer or use a Lambda container image.
