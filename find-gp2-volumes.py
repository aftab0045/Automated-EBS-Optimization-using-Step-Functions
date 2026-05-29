import boto3
from datetime import datetime

ec2 = boto3.client('ec2')

def lambda_handler(event, context):

    response = ec2.describe_volumes(
        Filters=[
            {
                'Name': 'volume-type',
                'Values': ['gp2']
            }
        ]
    )

    matched_volumes = []

    for volume in response['Volumes']:

        tags = volume.get('Tags', [])

        tag_match = any(
            tag['Key'] == 'AutoConvert' and tag['Value'].lower() == 'true'
            for tag in tags
        )

        if tag_match:

            instance_id = "Not Attached"

            if volume.get('Attachments'):
                instance_id = volume['Attachments'][0]['InstanceId']

            matched_volumes.append({
                'VolumeId': volume['VolumeId'],
                'InstanceId': instance_id,
                'VolumeType': volume['VolumeType'],
                'Size': volume['Size'],
                'Region': 'ap-south-1',
                'Timestamp': datetime.utcnow().isoformat()
            })

    print("Matched Volumes:", matched_volumes)

    return {
        'statusCode': 200,
        'Volumes': matched_volumes
    }