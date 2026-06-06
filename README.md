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

![](./img/Architecture%20Dig.png)

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
![](./img/Screenshot%202026-05-28%20180221.png)

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

![](./img/Screenshot%202026-05-28%20180608.png)

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

![](./img/Screenshot%202026-05-28%20180649.png)

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
![](./img/Screenshot%202026-05-28%20181050.png)

![](./img/Screenshot%202026-05-28%20181105.png)
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

![](./img/Screenshot%202026-05-28%20181144.png)

---

# Step 8 — Verify Attached Volume

Go to:

```text
EC2 → Instance → Storage
```

Verify both volumes are attached.

![](./img/Screenshot%202026-05-28%20181256.png)
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
![](./img/Screenshot%202026-05-28%20181540.png)
![](./img/Screenshot%202026-05-28%20181839.png)

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

![](./img/Screenshot%202026-05-28%20183040.png)

![](./img/Screenshot%202026-05-28%20183227.png)

---

# Step 3 — Create Email Subscription

Create subscription:

| Setting  | Value      |
| -------- | ---------- |
| Protocol | Email      |
| Endpoint | Your Email |

IMPORTANT:

Confirm subscription using the email received from AWS.


![](./img/Screenshot%202026-05-28%20183510.png)
![](./img/Screenshot%202026-05-28%20183525.png)
![](./img/Screenshot%202026-05-28%20183715.png)
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
![](./img/Screenshot%202026-05-28%20184042.png)

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
![](./img/Screenshot%202026-05-28%20184303.png)

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

![](./img/Screenshot%202026-05-28%20185116.png)
![](./img/Screenshot%202026-05-28%20185301.png)


---

## 2. Log Audit Lambda

Stores:

* Volume ID
* Timestamp
* Region
* Instance ID
* Volume Type

inside DynamoDB.

![](./img/Screenshot%202026-05-28%20185740.png)
![](./img/Screenshot%202026-05-28%20185815.png)


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

![](./img/Screenshot%202026-05-28%20185935.png)
![](./img/Screenshot%202026-05-28%20190023.png)

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

![](./img/Screenshot%202026-05-28%20190136.png)
![](./img/Screenshot%202026-05-28%20190217.png)

---

## 5. SNS Notification Lambda

Publishes SNS email alerts containing:

* Volume ID
* Conversion status
* Region

![](./img/Screenshot%202026-05-28%20190527.png)

---
## Manual Testing of Individual Lambda Functions

Before integrating all Lambda functions into the Step Functions workflow, each Lambda was tested individually to verify functionality, permissions, data flow, and error handling. This validation ensured that every component was working correctly before building the complete automation pipeline.

### Test 1 – Find GP2 Volumes Lambda

The **find-gp2-volumes** Lambda function was tested to verify that it successfully scans EBS volumes and filters only those that meet the following conditions:

* Volume Type = gp2
* Tag AutoConvert = true

The successful response confirmed that the Lambda was able to identify eligible volumes for optimization.

#### Successful Execution Output

![](./img/Screenshot%202026-05-28%20185553.png)

---

### Test 2 – Log EBS Audit Lambda

The **log-ebs-audit** Lambda function was tested using the output generated from the previous Lambda. The purpose of this test was to verify that volume details are successfully stored in the DynamoDB audit table.

#### Lambda Execution Test

![](./img/Screenshot%202026-05-28%20191626.png)

#### Successful Lambda Response

![](./img/Screenshot%202026-05-28%20191732.png)

#### DynamoDB Audit Records Successfully Created

The following screenshot confirms that the volume information was successfully stored in the **EBSVolumeAudit** DynamoDB table.

![](./img/Screenshot%202026-05-28%20191843.png)

---

### Test 3 – Convert GP2 to GP3 Lambda

The **convert-gp2-gp3** Lambda function was tested to verify that it successfully initiates the EBS volume modification process from gp2 to gp3.

#### Lambda Conversion Test

![](./img/Screenshot%202026-05-28%20192022.png)

#### Successful Conversion Request Initiated

The Lambda returned a successful response indicating that the volume modification process had started.

![](./img/Screenshot%202026-05-28%20192055.png)

---

### Test 4 – Verify Volume Modification Lambda

The **verify-volume-modification** Lambda function was tested to monitor the status of the EBS modification process and confirm whether the conversion was completed successfully.

#### Verification Lambda Test

![](./img/Screenshot%202026-05-28%20193156.png)

#### Successful Verification Response

The Lambda successfully returned the modification status of the target EBS volume.

![](./img/Screenshot%202026-05-28%20193219.png)

---

### Test 5 – SNS Notification Lambda

The **send-ebs-notification** Lambda function was tested to verify that email notifications are sent through Amazon SNS after a successful volume modification.

#### SNS Notification Test

![](./img/Screenshot%202026-05-28%20193326.png)

#### Successful SNS Publish Response


![](./img/Screenshot%202026-05-28%20193338.png)

#### Email Notification Received Successfully

The following screenshot confirms that the notification email was successfully delivered to the subscribed email address.

![](./img/Screenshot%202026-05-28%20193359.png)

---

### Verification of EBS Volume Conversion

After completing all Lambda tests successfully, the EBS volume was verified in the EC2 console to confirm that the volume type had been changed from **gp2** to **gp3**.

#### EBS Volume Successfully Converted from GP2 to GP3

![](./img/Screenshot%202026-05-28%20193911.png)

---

### Testing Conclusion

All Lambda functions were validated independently before integrating them into the Step Functions workflow. This testing phase confirmed:

* Successful identification of eligible gp2 volumes
* Successful audit logging into DynamoDB
* Successful EBS volume conversion from gp2 to gp3
* Successful verification of modification status
* Successful SNS email notification delivery

With all components verified, the project was ready for Step Functions orchestration and EventBridge automation.

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
![](/img/Screenshot%202026-05-28%20194604.png)
![](/img/Screenshot%202026-05-28%20194625.png)

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
![](/img/Screenshot%202026-05-28%20194822.png)
![](/img/Screenshot%202026-05-28%20194849.png)

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

![](/img/Screenshot%202026-05-28%20195009.png)
![](/img/Screenshot%202026-05-28%20195054.png)
![](/img/Screenshot%202026-05-28%20195110.png)

---

# Verification Performed

## Verified Components

### EC2 & EBS

* gp2 volume detection
* gp3 conversion

![](/img/Screenshot%202026-05-28%20195130.png)

### DynamoDB

* audit entries stored successfully

![](/img/Screenshot%202026-05-28%20195532.png)

### SNS

* email alerts received

![](/img/Screenshot%202026-05-28%20195159.png)

![](/img/Screenshot%202026-05-28%20202951.png)

### Step Functions

* successful execution states

![](/img/Screenshot%202026-05-28%20202210.png)


### EventBridge

* automatic scheduled execution

![](/img/Screenshot%202026-05-28%20202454.png)

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

# Conclusion

This project provides a real-world implementation of intelligent cloud automation using AWS serverless services.

It demonstrates:

* Event-driven architecture
* Automated infrastructure optimization
* Monitoring and logging
* Secure IAM design
* Workflow orchestration using Step Functions

The project is highly useful for understanding production-grade AWS automation pipelines and serverless cloud operations.
