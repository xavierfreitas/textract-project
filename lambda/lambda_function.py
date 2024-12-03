import boto3
import json
import os
from botocore.exceptions import ClientError

def handler(event, context):
    # Initialize Textract client
    textract = boto3.client('textract')

    # Get the bucket name from environment variable
    bucket_name = os.environ['UPLOAD_BUCKET']

    # Get 'fileKey' from query parameters
    file_key = None

    if 'queryStringParameters' in event and event['queryStringParameters']:
        file_key = event['queryStringParameters'].get('fileKey')
    
    if not file_key:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'fileKey parameter is required'}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }

    print(f"Processing file {file_key} from bucket {bucket_name}")

    try:
        # Check if the file exists in S3
        s3 = boto3.client('s3')
        s3.head_object(Bucket=bucket_name, Key=file_key)

        # Call Textract to analyze the document
        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': file_key
                }
            }
        )

        # Extract detected text
        extracted_text = ""
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE':
                extracted_text += item['Text'] + "\n"

        print("Extracted Text:")
        print(extracted_text)

        # Return the extracted text
        return {
            'statusCode': 200,
            'body': json.dumps({'extracted_text': extracted_text}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"File {file_key} not found in bucket {bucket_name}")
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'File not found'}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        else:
            print(f"Error accessing file {file_key}: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Error accessing file'}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
    except Exception as e:
        print(f"Error processing file {file_key}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to process file'}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
