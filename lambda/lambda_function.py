import boto3
import json

def handler(event, context):
    # Initialize Textract client
    textract = boto3.client('textract')

    # Parse S3 event to get bucket name and file key
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        file_key = record['s3']['object']['key']

        print(f"Processing file {file_key} from bucket {bucket_name}")

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

        # Return the extracted text as a log (or process it further)
        return {
            'statusCode': 200,
            'body': json.dumps({'extracted_text': extracted_text})
        }
