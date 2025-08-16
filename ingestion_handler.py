import json
import boto3
import os
from src.gmail_service import get_gmail_service, get_latest_email
from src.database_service import setup_database, save_message

# Initialize outside the handler for reuse ("cold start" optimization)
setup_database()
gmail_service = get_gmail_service()
sqs_client = boto3.client('sqs')

# Get the SQS Queue URL from an environment variable set by the CDK
NEW_QUERY_QUEUE_URL = os.getenv('NEW_QUERY_QUEUE_URL')

def handler(event, context):
    """
    This Lambda is the ingestion entry point. It's triggered by a Gmail push
    notification via API Gateway. It fetches the email, saves it to RDS,
    and places a job on the SQS queue for the main agent to process.
    """
    print("--- Ingestion Lambda Triggered ---")
    
    if not gmail_service:
        print("❌ Gmail service not available. Exiting.")
        return {'statusCode': 500, 'body': 'Gmail service not configured.'}
        
    if not NEW_QUERY_QUEUE_URL:
        print("❌ SQS Queue URL not configured. Exiting.")
        return {'statusCode': 500, 'body': 'SQS Queue URL not configured.'}

    # In a real app, parse the push notification from the 'event' body.
    # For now, fetch the latest unread email as a demonstration.
    email_data = get_latest_email(gmail_service)

    if email_data:
        try:
            thread_id = email_data["thread_id"]
            user_question = email_data["body"]
            user_email = email_data["sender"]

            # 1. Save the user's new message to the database
            save_message(thread_id, user_email, "user", user_question)
            print(f"✅ Message for thread {thread_id} saved to RDS.")

            # 2. Create a job message for the main agent
            message_body = {
                "thread_id": thread_id,
                "user_question": user_question,
                "original_email": email_data
            }

            # 3. Send the job to the SQS queue
            sqs_client.send_message(
                QueueUrl=NEW_QUERY_QUEUE_URL,
                MessageBody=json.dumps(message_body)
            )
            print(f"✅ Job for thread {thread_id} sent to SQS.")
            
            # Acknowledge the push notification
            return {'statusCode': 200, 'body': 'Email processed successfully.'}

        except Exception as e:
            print(f"❌ An error occurred during ingestion: {e}")
            return {'statusCode': 500, 'body': 'Internal server error.'}
    
    return {'statusCode': 200, 'body': 'No new emails to process.'}
