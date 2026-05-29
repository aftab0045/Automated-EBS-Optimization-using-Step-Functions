import boto3

ec2 = boto3.client('ec2')

def lambda_handler(event, context):

    volumes = event['Volumes']

    verification_results = []

    for volume in volumes:

        volume_id = volume['VolumeId']

        response = ec2.describe_volumes_modifications(
            VolumeIds=[volume_id]
        )

        modifications = response.get('VolumesModifications', [])

        if modifications:

            state = modifications[0]['ModificationState']

        else:
            state = "No Modification Found"

        verification_results.append({
            'VolumeId': volume_id,
            'Status': state
        })

    print("Verification Results:", verification_results)

    return {
        'Volumes': verification_results
    }