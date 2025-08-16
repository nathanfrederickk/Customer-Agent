import json
from src.graph import build_graph
from src.gmail_service import get_gmail_service
from src.database_service import setup_database, get_conversation_history, save_message

# --- Global Setup ---
print("Lambda container starting up...")
setup_database()
gmail_service = get_gmail_service()
app = build_graph(gmail_service=gmail_service)
print("🚀 LangGraph workflow compiled and ready.")

def handler(event, context):
    """
    This is the main entry point for the Lambda function.
    It is triggered by messages from the SQS queue.
    """
    print(f"Received {len(event['Records'])} message(s) from SQS.")
    
    for record in event['Records']:
        try:
            # The message body from the ingestion Lambda will be a JSON string
            message_body = json.loads(record['body'])
            thread_id = message_body['thread_id']
            user_question = message_body['user_question']
            original_email = message_body['original_email']

            print(f"--- Processing Thread ID: {thread_id} ---")

            # 1. Fetch the complete conversation history from the database
            chat_history = get_conversation_history(thread_id)

            # 2. Prepare the input for the LangGraph application
            inputs = {
                "question": user_question,
                "original_email": original_email,
                "chat_history": chat_history
            }
            
            print("\n--- Invoking Agent Workflow ---")
            final_state = None
            final_state = app.invoke(inputs)
            
            # 3. Save the agent's final response if it was approved
            if final_state:
                manager_decision = final_state.get("final_decision", {})
                if manager_decision.get("decision") == "send":
                    agent_reply = final_state.get("drafted_answer")
                    if agent_reply:
                        save_message(thread_id, original_email['sender'], "agent", agent_reply)
                        print("✅ Agent's reply saved to database.")

            print("\n--- Workflow Complete ---")

        except Exception as e:
            print(f"❌ An error occurred processing a message: {e}")
            # In a production system, move this message to a Dead-Letter Queue (DLQ)
            continue
            
    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete.')
    }
