## Clefer AI - Easy Grade, Property of Ryze Educational Tech Pvt Ltd

import boto3
import import_helper as ih

aws_cred = ih.get_env_val("AWS_CRED")
bkt_name = ih.get_env_val("AWS_BUCKET")

def s3_client():
  return (boto3.client("s3", **aws_cred))

def write_to_sys(file_path, s3_path):
  s3_client().download_file(bkt_name, s3_path, file_path)

def write_to_s3(file_path, s3_path):
  s3_client().upload_file(file_path, bkt_name, s3_path)

def delete_file(s3_path):
  s3_client().delete_object(Bucket=bkt_name, Key=s3_path)

## EOF
