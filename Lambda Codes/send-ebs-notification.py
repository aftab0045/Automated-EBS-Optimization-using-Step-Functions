import boto3

sns = boto3.client('sns')

SNS_TOPIC_ARN = 'PASTE_YOUR_ARN'

def lambda_handler(event, context):

    volumes = event['Volumes']

    for volume in volumes:

        message = f"""
EBS Volume Conversion Status

Volume ID: {volume['VolumeId']}
Status: {volume['Status']}
Region: ap-south-1
"""

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject='EBS Volume Converted',
            Message=message
        )

    print("SNS Notification Sent")

    return {
        'statusCode': 200
    }