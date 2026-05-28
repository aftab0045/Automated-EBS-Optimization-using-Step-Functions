# Intelligent EBS Volume Optimization Using Lambda, Step Functions, SNS, DynamoDB & EventBridge

## Project Overview

This project demonstrates a fully automated AWS serverless solution that intelligently detects Amazon EBS gp2 volumes and converts them into gp3 volumes using AWS Lambda and AWS Step Functions.

The workflow includes:

* Automated EBS volume discovery
* gp2 to gp3 conversion
* DynamoDB audit logging
* SNS email notifications
* Step Functions orchestration
* EventBridge scheduling
* CloudWatch logging and monitoring

This project simulates a real-world cloud cost optimization and automation scenario.

---

# Problem Statement

In AWS environments, many EBS volumes continue using the older `gp2` storage type even though `gp3` offers:

* Better performance
* Lower cost
* Independent IOPS scaling
* Better optimization

Manually identifying and converting volumes becomes difficult in large environments.

This project solves that problem by building an intelligent automation pipeline that:

1. Detects gp2 volumes automatically
2. Filters only tagged volumes
3. Converts them to gp3
4. Stores audit logs
5. Sends notifications
6. Runs automatically on schedule

---

# Project Architecture

```text
EventBridge Scheduler
        ↓
Step Functions Workflow
        ↓
Find gp2 Volumes Lambda
        ↓
Log Audit to DynamoDB
        ↓
Convert gp2 → gp3
        ↓
Wait State
        ↓
Verify Modification
        ↓
SNS Notification
```

---

# AWS Services Used

| Service            | Purpose                          |
| ------------------ | -------------------------------- |
| Amazon EC2         | Host attached EBS volumes        |
| Amazon EBS         | Storage volumes for optimization |
| AWS Lambda         | Serverless automation logic      |
| AWS Step Functions | Workflow orchestration           |
| Amazon DynamoDB    | Audit logging                    |
| Amazon SNS         | Email notifications              |
| Amazon EventBridge | Scheduled execution              |
| AWS IAM            | Secure permissions               |
| Amazon CloudWatch  | Logs and monitoring              |

---

# Phase 1 — Base Infrastructure Setup

## Step 1 — Login to AWS Console

Login to the AWS Management Console.

---

## Step 2 — Select Region

Select:

```text
Asia Pacific (Mumbai)
ap-south-1
```

IMPORTANT:

All services must remain in the same region.

Otherwise:

* Lambda cannot find volumes
* SNS issues occur
* DynamoDB mismatches happen
* Step Function execution fails

---

# Step 3 — Create IAM Role for EC2

Go to:

```text
IAM → Roles → Create Role
```

### Trusted Entity

Select:

* AWS Service
* EC2

### Attach Policy

Attach:

```text
AmazonSSMManagedInstanceCore
```

### Role Name

```text
ec2-ebs-demo-role
```

### Why This Role?

This allows:

* Session Manager access
* Secure EC2 management
* No SSH key dependency

---

# Step 4 — Launch EC2 Instance

Go to:

```text
EC2 → Launch Instance
```

## Configuration

| Setting       | Value             |
| ------------- | ----------------- |
| Name          | ebs-demo-server   |
| AMI           | Amazon Linux 2023 |
| Instance Type | t2.micro          |
| Key Pair      | None              |
| VPC           | Default           |
| Public IP     | Enabled           |

---

## Security Group

Recommended:

* No inbound rules

Optional:

* Allow SSH from My IP

---

## Root Volume Configuration

IMPORTANT:

Change root volume type from:

```text
gp3 → gp2
```

| Setting | Value |
| ------- | ----- |
| Size    | 10 GB |
| Type    | gp2   |

---

## IAM Instance Profile

Attach:

```text
ec2-ebs-demo-role
```

Launch instance.

---

# Step 5 — Verify Root Volume

Go to:

```text
EC2 → Volumes
```

Ensure:

| Property | Expected |
| -------- | -------- |
| Type     | gp2      |
| State    | in-use   |

---

# Step 6 — Create Additional gp2 Volume

Go to:

```text
EC2 → Volumes → Create Volume
```

## Configuration

| Setting | Value       |
| ------- | ----------- |
| Type    | gp2         |
| Size    | 5 GB        |
| AZ      | Same as EC2 |

---

## Tags

Add:

| Key         | Value                   |
| ----------- | ----------------------- |
| Name        | ebs-auto-convert-volume |
| AutoConvert | true                    |

IMPORTANT:

The Lambda scans only volumes tagged:

```text
AutoConvert=true
```

---

# Step 7 — Attach Volume

Attach volume to:

```text
ebs-demo-server
```

Device:

```text
/dev/xvdf
```

---

# Step 8 — Verify Attached Volume

Go to:

```text
EC2 → Instance → Storage
```

Verify both volumes are attached.

---

# Step 9 — Connect Using Session Manager

Use:

```text
EC2 → Connect → Session Manager
```

---

# Step 10 — Verify Disk Inside Linux

Run:

```bash
lsblk
```

Expected:

```text
xvda
xvdf
```

---

# Phase 2 — Create Supporting AWS Services

---

# Step 1 — Create DynamoDB Table

Go to:

```text
DynamoDB → Create Table
```

## Table Configuration

| Setting       | Value          |
| ------------- | -------------- |
| Table Name    | EBSVolumeAudit |
| Partition Key | VolumeId       |
| Sort Key      | Timestamp      |

Capacity mode:

```text
On-demand
```

---

# Step 2 — Create SNS Topic

Go to:

```text
SNS → Create Topic
```

## Configuration

| Setting | Value             |
| ------- | ----------------- |
| Type    | Standard          |
| Name    | ebs-volume-alerts |

---

# Step 3 — Create Email Subscription

Create subscription:

| Setting  | Value      |
| -------- | ---------- |
| Protocol | Email      |
| Endpoint | Your Email |

IMPORTANT:

Confirm subscription using the email received from AWS.

---

# Step 4 — Create IAM Role for Lambda

Create role:

```text
lambda-ebs-optimization-role
```

Attach policies:

```text
AmazonEC2FullAccess
AmazonDynamoDBFullAccess
AmazonSNSFullAccess
CloudWatchLogsFullAccess
```

---

# Step 5 — Create IAM Role for Step Functions

Create role:

```text
stepfunction-ebs-role
```

Attach:

```text
AWSLambdaRole
AWSStepFunctionsFullAccess
```

---

# Phase 3 — Create Lambda Functions

All Lambdas use:

| Setting      | Value                        |
| ------------ | ---------------------------- |
| Runtime      | Python 3.12                  |
| Architecture | x86_64                       |
| Role         | lambda-ebs-optimization-role |

---

# Lambda Functions Created

| Lambda Name                | Purpose                |
| -------------------------- | ---------------------- |
| find-gp2-volumes           | Detect gp2 volumes     |
| log-ebs-audit              | Store logs in DynamoDB |
| convert-gp2-gp3            | Convert volumes        |
| verify-volume-modification | Verify conversion      |
| send-ebs-notification      | Send SNS alerts        |

---

# Lambda Workflow

## 1. Find Volumes Lambda

Scans:

* gp2 volumes
* tagged AutoConvert=true

Returns matching volumes.

---

## 2. Log Audit Lambda

Stores:

* Volume ID
* Timestamp
* Region
* Instance ID
* Volume Type

inside DynamoDB.

---

## 3. Convert Lambda

Uses:

```python
ec2.modify_volume()
```

to convert:

```text
gp2 → gp3
```

---

## 4. Verify Lambda

Checks:

* modifying
* optimizing
* completed

using:

```python
describe_volumes_modifications()
```

---

## 5. SNS Notification Lambda

Publishes SNS email alerts containing:

* Volume ID
* Conversion status
* Region

---

# Lambda Testing Flow

Each Lambda was tested individually using test events.

Verification included:

* CloudWatch logs
* DynamoDB entries
* Volume conversion
* SNS emails

---

# Phase 4 — Step Functions Workflow

## Workflow

```text
Find Volumes
      ↓
Log DynamoDB
      ↓
Convert Volume
      ↓
Wait 30 Seconds
      ↓
Verify Conversion
      ↓
Send Notification
```

---

# Create Step Function

Go to:

```text
Step Functions → Create State Machine
```

## Configuration

| Setting | Value                   |
| ------- | ----------------------- |
| Type    | Standard                |
| Name    | EBSOptimizationWorkflow |

Role:

```text
stepfunction-ebs-role
```

---

# Step Function Features

* Visual workflow execution
* Central orchestration
* Retry capability
* State tracking
* Debugging support

---

# Manual Workflow Execution

Use:

```json
{}
```

as execution input.

The workflow:

1. Finds volumes
2. Logs data
3. Converts volumes
4. Verifies conversion
5. Sends email notifications

---

# Phase 5 — EventBridge Automation

The workflow was automated using EventBridge Scheduler.

---

# EventBridge Rule Configuration

| Setting       | Value                   |
| ------------- | ----------------------- |
| Rule Type     | Schedule                |
| Schedule      | rate(5 minutes)         |
| Target        | Step Functions          |
| State Machine | EBSOptimizationWorkflow |

---

# Automatic Execution Flow

```text
EventBridge
      ↓
Step Functions
      ↓
Lambda Workflow
      ↓
SNS Notification
```

---

# Verification Performed

## Verified Components

### EC2 & EBS

* gp2 volume detection
* gp3 conversion

### DynamoDB

* audit entries stored successfully

### SNS

* email alerts received

### Step Functions

* successful execution states

### EventBridge

* automatic scheduled execution

### CloudWatch

* Lambda logs generated successfully

---

# Security Best Practices Used

## IAM Roles

Separate IAM roles were used for:

* EC2
* Lambda
* Step Functions

---

## Scoped Resource Access

Only required AWS services were granted access.

---

## Session Manager Instead of SSH

Improved security by avoiding public SSH access.

---

## No Hardcoded Credentials

AWS IAM roles were used instead of access keys.

---

# Common Issues Faced

| Issue                           | Solution                                    |
| ------------------------------- | ------------------------------------------- |
| Volume not detected             | Added AutoConvert=true tag                  |
| Volume attach failed            | Used same AZ                                |
| SNS email not received          | Confirmed subscription                      |
| Lambda access denied            | Fixed IAM policies                          |
| Step Function validation failed | Corrected Lambda ARN                        |
| EventBridge rule failed         | Used Schedule rule instead of Event Pattern |

---

# Final Project Outcome

Successfully built a complete AWS serverless automation pipeline that:

* Detects gp2 EBS volumes
* Converts them into gp3
* Stores audit history
* Sends notifications
* Runs automatically on schedule

This project demonstrates practical implementation of:

* Serverless computing
* Cloud automation
* AWS orchestration
* Monitoring and alerting
* Infrastructure optimization

---

# Future Enhancements

Possible future improvements:

* Least privilege IAM policies
* Multi-region support
* Slack notifications
* Auto rollback support
* Cost analytics dashboard
* AWS Config integration
* CloudFormation/Terraform deployment

---

# Conclusion

This project provides a real-world implementation of intelligent cloud automation using AWS serverless services.

It demonstrates:

* Event-driven architecture
* Automated infrastructure optimization
* Monitoring and logging
* Secure IAM design
* Workflow orchestration using Step Functions

The project is highly useful for understanding production-grade AWS automation pipelines and serverless cloud operations.
