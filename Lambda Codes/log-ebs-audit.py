import boto3

dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table('EBSVolumeAudit')

def lambda_handler(event, context):

    volumes = event['Volumes']

    for volume in volumes:

        table.put_item(
            Item={
                'VolumeId': volume['VolumeId'],
                'Timestamp': volume['Timestamp'],
                'InstanceId': volume['InstanceId'],
                'VolumeType': volume['VolumeType'],
                'Size': str(volume['Size']),
                'Region': volume['Region']
            }
        )

    print("Logged volumes into DynamoDB")

    return event