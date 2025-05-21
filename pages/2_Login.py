import streamlit as st
from db import get_connection

# Page configuration
st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")

# Custom CSS for better styling (using Streamlit's built-in methods)
st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            padding: 2rem;
            margin: auto;
        }
        .stRadio > div {
            display: flex;
            justify-content: space-around;
        }
        .stButton > button {
            width: 100%;
            padding: 0.5rem;
            border-radius: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)


# Main login function
def main():
    st.title("🔐 Login")
    
    # Login type selection
    login_type = st.radio(
        "Login as:",
        ("User", "Organization"),
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # Form container
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="your@email.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        # Remember me checkbox
        remember_me = st.checkbox("Remember me")
        
        # Form submit button
        submitted = st.form_submit_button("Login", type="primary")
        
        if submitted:
            if not email or not password:
                st.error("Please fill in all fields")
                return
            
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            
            if login_type == "User":
                handle_user_login(cursor, email, password)
            else:
                handle_org_login(cursor, email, password)
            
            conn.close()

    # Additional options
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Forgot Password?"):
            st.info("Password reset feature coming soon!")
    with col2:
        if st.button("Create Account"):
            st.switch_page("pages/1_Sign_Up.py")  # Assuming you have a registration page

# Handle user login
def handle_user_login(cursor, email, password):
    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cursor.fetchone()
    
    if user:
        st.success(f"👋 Welcome back, {user['name']}!")
        st.session_state.user = user
        st.session_state.user_type = "User"
        st.session_state.user_id = user["id"]
        st.rerun()  # Refresh to show logged-in state
    else:
        st.error("❌ Invalid email or password for user account")

# Handle organization login
def handle_org_login(cursor, email, password):
    cursor.execute("""
        SELECT * FROM organizations 
        WHERE email=%s AND password=%s AND is_approved=1
    """, (email, password))
    organization = cursor.fetchone()
    
    if organization:
        if not organization["is_active"]:
            st.error("⛔ Your organization account has been deactivated")
            return
            
        st.success(f"🏢 Welcome, {organization['org_name']}!")
        st.session_state.organization = organization
        st.session_state.user_type = "Organization"
        st.session_state.organization_id = organization["id"]
        st.rerun()  # Refresh to show logged-in state
    else:
        cursor.execute("SELECT * FROM organizations WHERE email=%s", (email,))
        exists = cursor.fetchone()
        
        if exists:
            if not exists["is_approved"]:
                st.error("⏳ Your organization registration is pending approval")
            else:
                st.error("❌ Invalid password for organization account")
        else:
            st.error("❌ No organization found with this email")


# Show different content if already logged in
if st.session_state.get("user"):
    st.success(f"✅ You're logged in as User: {st.session_state.user['name']}")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
        
elif st.session_state.get("organization"):
    org = st.session_state.organization
    st.success(f"✅ You're logged in as Organization: {org['org_name']}")
    
    # Show organization status
    status = "Approved ✅" if org["is_approved"] else "Pending Approval ⏳"
    st.info(f"Organization Status: {status}")
    
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
else:
    main()