import psycopg2
import os
from utils.secret_manager import get_secret

db_secret_data = get_secret("prod/CustomerAgent/DatabasePassword")

# --- Database Connection ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = db_secret_data['password']
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")


def get_db_connection():
    """Establishes a connection to the PostgreSQL database using environment variables."""
    # Check if all required environment variables are set. This is a crucial health check.
    if not all([DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT]):
        print("❌ Database environment variables are not fully configured. Cannot connect.")
        return None
    
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Could not connect to the database: {e}")
        return None

def setup_database():
    """
    Connects to the database and creates the necessary tables if they don't exist.
    This should be called once on application startup.
    """
    print("Attempting to set up database tables...")
    conn = get_db_connection()
    if not conn:
        print("Aborting database setup due to connection failure.")
        return
        
    with conn.cursor() as cur:
        # Create the 'conversations' table to track email threads
        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                thread_id VARCHAR(255) PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                status VARCHAR(50) DEFAULT 'open',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Create the 'messages' table to store individual messages
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id SERIAL PRIMARY KEY,
                thread_id VARCHAR(255) REFERENCES conversations(thread_id),
                sender VARCHAR(50) NOT NULL, -- 'user' or 'agent'
                content TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.commit()
    conn.close()
    print("✅ Database tables are set up successfully.")

def save_message(thread_id, user_email, sender, content):
    """Saves a new message to the database for a specific conversation thread."""
    conn = get_db_connection()
    if not conn:
        return
        
    with conn.cursor() as cur:
        # First, ensure the conversation record exists. If it does, this does nothing.
        cur.execute(
            "INSERT INTO conversations (thread_id, user_email) VALUES (%s, %s) ON CONFLICT (thread_id) DO NOTHING;",
            (thread_id, user_email)
        )
        # Then, insert the new message
        cur.execute(
            "INSERT INTO messages (thread_id, sender, content) VALUES (%s, %s, %s);",
            (thread_id, sender, content)
        )
    conn.commit()
    conn.close()

def get_conversation_history(thread_id):
    """Retrieves and formats the conversation history for a given thread_id."""
    conn = get_db_connection()
    if not conn:
        return "" # Return an empty string if the DB connection fails
        
    history = []
    with conn.cursor() as cur:
        cur.execute(
            "SELECT sender, content FROM messages WHERE thread_id = %s ORDER BY created_at ASC;",
            (thread_id,)
        )
        for record in cur.fetchall():
            sender, content = record
            history.append(f"{sender.capitalize()}: {content}")
    
    conn.close()
    
    # Format the history into a simple string for the LLM
    return "\n".join(history)
