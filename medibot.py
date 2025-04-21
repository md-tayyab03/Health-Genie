import os
import streamlit as st
import streamlit_authenticator as stauth
from models import ChatBot, ChatMessage
import yaml
from yaml.loader import SafeLoader
from dotenv import load_dotenv
from datetime import datetime
import re
import json
from pathlib import Path

# Load environment variables
load_dotenv()

# Constants
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CHAT_HISTORY_DIR = "chat_histories"

# Create chat history directory if it doesn't exist
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

# Initialize session states
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

def save_chat_history_to_file(username: str):
    """Save chat history to a file."""
    if username in st.session_state.chat_history:
        file_path = os.path.join(CHAT_HISTORY_DIR, f"{username}_chat_history.json")
        # Convert ChatMessage objects to dictionaries
        history_dict = {}
        for chat_id, chat_data in st.session_state.chat_history[username].items():
            history_dict[chat_id] = {
                "title": chat_data["title"],
                "timestamp": chat_data["timestamp"],
                "messages": [{"role": msg.role, "content": msg.content} for msg in chat_data["messages"]]
            }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history_dict, f, ensure_ascii=False, indent=2)

def load_chat_history_from_file(username: str):
    """Load chat history from file."""
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{username}_chat_history.json")
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            history_dict = json.load(f)
            # Convert dictionaries back to ChatMessage objects
            for chat_id, chat_data in history_dict.items():
                messages = [ChatMessage(role=msg["role"], content=msg["content"]) 
                          for msg in chat_data["messages"]]
                if username not in st.session_state.chat_history:
                    st.session_state.chat_history[username] = {}
                st.session_state.chat_history[username][chat_id] = {
                    "title": chat_data["title"],
                    "timestamp": chat_data["timestamp"],
                    "messages": messages
                }

def initialize_bot():
    """Initialize chatbot."""
    if not GOOGLE_API_KEY:
        st.error("Please set the GOOGLE_API_KEY environment variable.")
        st.stop()
    
    return ChatBot(GOOGLE_API_KEY)

def create_new_chat():
    """Create a new chat session."""
    chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.messages = []
    st.session_state.current_chat_id = chat_id
    if st.session_state["username"] not in st.session_state.chat_history:
        st.session_state.chat_history[st.session_state["username"]] = {}
    
    # Get the number of existing chats or start from 1 if empty
    chat_number = len(st.session_state.chat_history[st.session_state["username"]]) + 1
    if chat_number > 1 and len(st.session_state.chat_history[st.session_state["username"]]) == 0:
        chat_number = 1
        
    st.session_state.chat_history[st.session_state["username"]][chat_id] = {
        "messages": [],
        "title": f"Chat {chat_number}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def load_chat(chat_id):
    """Load a specific chat session."""
    if chat_id in st.session_state.chat_history[st.session_state["username"]]:
        st.session_state.messages = st.session_state.chat_history[st.session_state["username"]][chat_id]["messages"]
        st.session_state.current_chat_id = chat_id

def save_current_chat():
    """Save the current chat session."""
    if st.session_state.current_chat_id and st.session_state["username"] in st.session_state.chat_history:
        st.session_state.chat_history[st.session_state["username"]][st.session_state.current_chat_id]["messages"] = st.session_state.messages
        save_chat_history_to_file(st.session_state["username"])

def perform_logout():
    """Reset authentication state"""
    # Save chat history before clearing session
    if "username" in st.session_state:
        save_chat_history_to_file(st.session_state["username"])
    # Clear all session states
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def clear_chat_history():
    # """Clear all chat history for the current user except the current chat."""
    username = st.session_state["username"]
    current_chat_id = st.session_state.current_chat_id
    current_chat_data = None

    # Save current chat data if it exists
    if current_chat_id and username in st.session_state.chat_history:
        current_chat_data = st.session_state.chat_history[username].get(current_chat_id)

    # Clear chat history from session state
    if username in st.session_state.chat_history:
        st.session_state.chat_history[username] = {}
        
        # Restore only the current chat if it exists
        if current_chat_data:
            st.session_state.chat_history[username][current_chat_id] = current_chat_data
            st.session_state.messages = current_chat_data["messages"]
        else:
            st.session_state.messages = []
            st.session_state.current_chat_id = None

    # Update the chat history file
    file_path = os.path.join(CHAT_HISTORY_DIR, f"{username}_chat_history.json")
    if current_chat_data:
        # Save only the current chat
        with open(file_path, 'w', encoding='utf-8') as f:
            history_dict = {
                current_chat_id: {
                    "title": current_chat_data["title"],
                    "timestamp": current_chat_data["timestamp"],
                    "messages": [{"role": msg.role, "content": msg.content} 
                               for msg in current_chat_data["messages"]]
                }
            }
            json.dump(history_dict, f, ensure_ascii=False, indent=2)
    else:
        # If no current chat, delete the file
        if os.path.exists(file_path):
            os.remove(file_path)

def display_sidebar():
    """Display and manage sidebar content."""
    with st.sidebar:
        # Hide scrollbar
        st.markdown("""
            <style>
                [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
                    overflow: hidden;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Top container for New Chat
        top_container = st.container()
        with top_container:
            st.button("🗨️ New Chat", on_click=create_new_chat, use_container_width=True)
        
        # Chat History container
        history_container = st.container()
        with history_container:
            st.subheader("Chat History")
            if st.session_state["username"] in st.session_state.chat_history:
                for chat_id, chat_data in sorted(
                    st.session_state.chat_history[st.session_state["username"]].items(),
                    key=lambda x: x[1]["timestamp"],
                    reverse=True
                ):
                    if st.button(
                        f"{chat_data['title']}",
                        key=f"chat_{chat_id}",
                        use_container_width=True
                    ):
                        load_chat(chat_id)
        
        # Separation line before buttons
        st.markdown("---")
        
        # Action buttons container
        action_container = st.container()
        with action_container:
            # First row of buttons
            col1, col2 = st.columns(2)
            with col1:
                # Theme toggle button
                if 'is_dark_theme' not in st.session_state:
                    st.session_state.is_dark_theme = True
                
                if st.button("Theme", key="theme", help="Toggle Theme", use_container_width=True):
                    st.session_state.is_dark_theme = not st.session_state.is_dark_theme
                    # Apply theme change
                    if st.session_state.is_dark_theme:
                        st.markdown("""
                            <style>
                                :root {
                                    --primary-color: #2c3e50;
                                    --secondary-color: #34495e;
                                    --accent-color: #3498db;
                                    --text-color: #ecf0f1;
                                    --background-color: #1a1a1a;
                                }
                            </style>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                            <style>
                                :root {
                                    --primary-color: #ecf0f1;
                                    --secondary-color: #bdc3c7;
                                    --accent-color: #3498db;
                                    --text-color: #2c3e50;
                                    --background-color: #ffffff;
                                }
                            </style>
                        """, unsafe_allow_html=True)
            
            with col2:
                # Source toggle button
                if 'show_sources' not in st.session_state:
                    st.session_state.show_sources = False
                
                sources_text = "ON" if st.session_state.show_sources else "OFF"
                sources_help = "Click to turn sources OFF" if st.session_state.show_sources else "Click to turn sources ON"
                
                if st.button(sources_text, key="sources", help=sources_help, use_container_width=True):
                    st.session_state.show_sources = not st.session_state.show_sources
        
        # Bottom container
        bottom_container = st.container()
        with bottom_container:
            # Create two equal columns for Clear and Logout buttons
            col3, col4 = st.columns(2)
            
            # Clear Chat button in first column
            with col3:
                if st.button("Clear", key="clear_chat", help="Clear All Chats", use_container_width=True):
                    if st.session_state["username"] in st.session_state.chat_history:
                        st.session_state.chat_history[st.session_state["username"]] = {}
                    st.session_state.messages = []
                    st.session_state.current_chat_id = None
                    create_new_chat()  # Create a new Chat 1 after clearing
                    st.rerun()
            
            # Logout button in second column
            with col4:
                if st.button("Logout", key="logout_btn", help="Logout", use_container_width=True):
                    perform_logout()

def is_valid_email(email):
    """Validate email format."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def save_config(config):
    """Save the configuration to config.yaml file."""
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False)

def register_user(username, name, email, password):
    """Register a new user."""
    # Load current config
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    # Check if username already exists
    if username in config['credentials']['usernames']:
        return False, "Username already exists"
    
    # Check if email already exists
    for user_data in config['credentials']['usernames'].values():
        if user_data.get('email') == email:
            return False, "Email already registered"
    
    # Add new user
    config['credentials']['usernames'][username] = {
        'email': email,
        'name': name,
        'password': password  # In a production environment, this should be hashed
    }
    
    # Add email to preauthorized list if it doesn't exist
    if email not in config['preauthorized']['emails']:
        config['preauthorized']['emails'].append(email)
    
    # Save updated config
    save_config(config)
    return True, "Registration successful"

def main():
    st.set_page_config(page_title="HealthGenie", page_icon="🏥", layout="wide")
    
    # Load config file
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    # Get credentials
    credentials = config['credentials']
    
    # Simple login form
    if "authentication_status" not in st.session_state:
        st.session_state["authentication_status"] = None
    
    if st.session_state["authentication_status"] != True:
        st.title("🏥 HealthGenie - Login")
        
        # Create tabs for Login and Register
        login_tab, register_tab = st.tabs(["Login", "Register"])
        
        with login_tab:
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", key="login_button"):
                if username in credentials['usernames']:
                    # Compare the passwords directly for admin
                    if username == "admin" and password == "admin":
                        st.session_state["authentication_status"] = True
                        st.session_state["username"] = username
                        st.session_state["name"] = credentials['usernames'][username]['name']
                        # Load chat history after successful login
                        load_chat_history_from_file(username)
                        st.rerun()
                    # For other users
                    elif password == credentials['usernames'][username]['password']:
                        st.session_state["authentication_status"] = True
                        st.session_state["username"] = username
                        st.session_state["name"] = credentials['usernames'][username]['name']
                        # Load chat history after successful login
                        load_chat_history_from_file(username)
                        st.rerun()
                    else:
                        st.error("Invalid password")
                else:
                    st.error("Invalid username")
        
        with register_tab:
            with st.form("registration_form"):
                new_username = st.text_input("Username", key="reg_username")
                new_password = st.text_input("Password", type="password", key="reg_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
                new_name = st.text_input("Full Name", key="reg_name")
                new_email = st.text_input("Email", key="reg_email")
                
                submit_button = st.form_submit_button("Register")
                
                if submit_button:
                    if not all([new_username, new_password, confirm_password, new_name, new_email]):
                        st.error("Please fill in all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif not is_valid_email(new_email):
                        st.error("Please enter a valid email address")
                    else:
                        success, message = register_user(new_username, new_name, new_email, new_password)
                        if success:
                            st.success(message)
                            st.info("Please go to the Login tab to sign in")
                        else:
                            st.error(message)
        return

    # If authenticated, show the main app
    if st.session_state["authentication_status"]:
        # Initialize chatbot
        chatbot = initialize_bot()
        
        # Create new chat if first login or no current chat
        if not st.session_state.current_chat_id:
            create_new_chat()
        
        # Display sidebar
        display_sidebar()
        
        # Display chat header
        st.title("🏥 HealthGenie - Medical Assistant")
        st.write("Ask me any medical questions, and I'll provide evidence-based information to help you understand health topics better.")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message.role):
                st.write(message.content)
        
        # Get user input
        if prompt := st.chat_input("What would you like to know about?"):
            st.session_state.messages.append(ChatMessage(role="user", content=prompt))
            
            # Get response with sources if enabled
            show_sources = st.session_state.get('show_sources', False)
            response = chatbot.generate_response(
                prompt=prompt,
                message_history=st.session_state.messages[-5:],  # Pass last 5 messages for context
                show_sources=show_sources  # Pass the sources toggle state
            )
            
            if response:
                result, final_result = response
                st.session_state.messages.append(
                    ChatMessage(role="assistant", content=final_result)
                )
                save_current_chat()
                st.rerun()

if __name__ == "__main__":
    main()