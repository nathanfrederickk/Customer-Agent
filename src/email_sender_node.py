# src/email_sender_node.py

from gmail_service import send_email

def email_sender_node(state, service):
    """
    Node for sending the final, approved email reply.
    
    Args:
        state (GraphState): The current state of the graph.
        service: The authenticated Gmail API service object.
    
    Returns:
        dict: An empty dictionary as this is a final step.
    """
    print("--- SENDING EMAIL REPLY ---")
    
    # Extract necessary info from the state
    original_email = state["original_email"]
    drafted_answer = state["drafted_answer"]
    
    recipient = original_email["sender"] # Reply to the original sender
    subject = "Re: " + original_email["subject"]
    thread_id = original_email["thread_id"]

    # Call the send_email function from our gmail_service
    send_email(
        service=service,
        to=recipient,
        subject=subject,
        message_text=drafted_answer,
        thread_id=thread_id
    )
    
    print("✅ Email sent successfully.")
    return {}
