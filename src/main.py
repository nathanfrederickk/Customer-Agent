# src/main_listener.py

import time
from gmail_service import get_gmail_service, get_latest_email
from graph import build_graph 

def main():
    """Main loop to check for new emails and process them with the agent."""
    print("Starting email listener...")
    service = get_gmail_service()
    if not service:
        print("Failed to connect to Gmail. Exiting.")
        return
        
    # Build the graph and pass the authenticated service to it
    app = build_graph(gmail_service=service)
    print("\n🚀 LangGraph workflow with Email Sender compiled!")

    while True:
        print("\nChecking for new emails...")
        email_data = get_latest_email(service)

        if email_data:
            inputs = {
                "question": email_data["body"],
                "original_email": email_data, 
                "chat_history": "" # Placeholder for now
            }
            
            print("\n--- Invoking Agent Workflow ---")
            for output in app.stream(inputs):
                for key, value in output.items():
                    print(f"Output from node '{key}':")
            
            print("\n--- Workflow Complete ---")

        time.sleep(30) # Check every 30 seconds

if __name__ == "__main__":
    main()
