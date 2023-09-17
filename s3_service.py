from config import *
from dotenv import load_dotenv
import boto3
import os
import logging
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename

s3_client = None

#This config is for ec2 instance configuration ez :3
if isEc2Instance:
    s3_client = boto3.client('s3')
else:
    load_dotenv()
    #This is for the local s3 dev environment
    s3_client = boto3.client(
        's3',
        aws_access_key_id= os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN')
    )
    
def uploadToS3(file, path):

    try:
        s3_client.upload_fileobj(
            file,
            custombucket,
            path,
        )
        #s3.Bucket(custombucket).put_object(Key=file_name, Body=file_content)
        object_url = get_object_url(path)
        print(f'Success, Uploaded File Object URL {object_url}')
        return True
    except Exception as e:
        print(str(e))
        return False

#Sample Function to Get the Object Url
def get_object_url(path):

    bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
    s3_location = (bucket_location['LocationConstraint'])

    if s3_location is None:
        s3_location = ''
    else:
        s3_location = '-' + s3_location

    object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
        s3_location,
        custombucket,
        path)
    
    return object_url



def list_files(student_id):
    """List files in AWS S3 bucket"""
    s3 = boto3.resource('s3')
    my_bucket = s3.Bucket(custombucket)

    # Key = path of the Object from bucket
    # last_modified = last modified date of the Object

    for obj in my_bucket.objects:
        print("Object Key : " + obj.key)
        print("Last Modified : " + obj.last_modified)


#Sample Implementation of List Reports
def getProgressionReports(student_id):
    s3 = boto3.resource('s3')
    my_bucket = s3.Bucket(custombucket)

    reports = []
    for obj in my_bucket.objects.filter(Prefix=f"students/{student_id}"):
        if obj.key == f"students/{student_id}/profile.png":
            print("Skipping profile.png")
        else:
            # report_info = {
            #     "url": get_object_url(obj.key),
            #     "key": obj.key,
            #     "last_modified": obj.last_modified.strftime("%Y-%m-%d %H:%M:%S")
            # }
            report_info = {
                get_object_url(obj.key),
            }
            reports.append(report_info)
            #print(report_info)

    return reports
