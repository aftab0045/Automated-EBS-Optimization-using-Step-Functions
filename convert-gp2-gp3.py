import boto3

ec2 = boto3.client('ec2')

def lambda_handler(event, context):

    volumes = event['Volumes']

    converted = []

    for volume in volumes:

        volume_id = volume['VolumeId']

        response = ec2.modify_volume(
            VolumeId=volume_id,
            VolumeType='gp3'
        )

        converted.append({
            'VolumeId': volume_id,
            'ModificationState': 'Started'
        })

    print("Conversion Started:", converted)

    return {
        'Volumes': converted
    }