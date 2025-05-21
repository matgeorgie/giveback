import streamlit as st
from db import get_connection

# Page configuration
st.set_page_config(page_title="Sign Up", page_icon="📝", layout="centered")

# Session state for form persistence and submission status
if "signup_data" not in st.session_state:
    st.session_state.signup_data = {}
if "signup_success" not in st.session_state:
    st.session_state.signup_success = False

st.title("Create Your Account")
st.caption("Join our platform to get started")

# Only show the form if we haven't had a successful submission yet
if not st.session_state.signup_success:
    # Signup type selection
    signup_type = st.radio(
        "Account Type:",
        ("User", "Organization"),
        horizontal=True,
        help="Select whether you're signing up as an individual or an organization"
    )

    with st.form("signup_form"):
        if signup_type == "User":
            st.subheader("User Information")
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input(
                    "Full Name*",
                    value=st.session_state.signup_data.get("name", ""),
                    help="Your full name as it should appear on your account"
                )
                
            with col2:
                email = st.text_input(
                    "Email*",
                    value=st.session_state.signup_data.get("email", ""),
                    help="We'll use this for account communication"
                )
            
            password = st.text_input(
                "Password*",
                type="password",
                help="Create a strong password with at least 8 characters"
            )
            
            address = st.text_area(
                "Address",
                value=st.session_state.signup_data.get("address", ""),
                help="Your current address"
            )
            
            phone = st.text_input(
                "Phone Number",
                value=st.session_state.signup_data.get("phone", ""),
                help="Include country code if international"
            )
            
        else:  # Organization
            st.subheader("Organization Information")
            
            org_name = st.text_input(
                "Organization Name*",
                value=st.session_state.signup_data.get("org_name", ""),
                help="The official name of your organization"
            )
            
            email = st.text_input(
                "Organization Email*",
                value=st.session_state.signup_data.get("email", ""),
                help="Official contact email for the organization"
            )
            
            password = st.text_input(
                "Password*",
                type="password",
                help="Create a strong password for your organization account"
            )
            
            description = st.text_area(
                "Organization Description",
                value=st.session_state.signup_data.get("description", ""),
                help="Briefly describe what your organization does"
            )
            
            address = st.text_area(
                "Organization Address*",
                value=st.session_state.signup_data.get("address", ""),
                help="Official address of your organization"
            )
            
            phone = st.text_input(
                "Contact Phone*",
                value=st.session_state.signup_data.get("phone", ""),
                help="Primary contact number for the organization"
            )
            
            st.subheader("Verification Details")
            
            gov_id_type = st.selectbox(
                "Government ID Type*",
                ["Aadhaar Card", "PAN Card", "Passport", "Driver's License", 
                 "Voter ID", "Business Registration", "Other"],
                index=0,
                help="Select the type of government-issued ID"
            )
            
            gov_id_number = st.text_input(
                "Government ID Number*",
                value=st.session_state.signup_data.get("gov_id_number", ""),
                help="Enter the ID number exactly as it appears"
            )
            
            gov_id_proof = st.file_uploader(
                "Upload Government ID Proof (Optional for Demo)",
                type=["pdf", "jpg", "png"],
                help="Upload a scanned copy of your government ID for verification"
            )
            
            if gov_id_proof:
                st.info("File upload functionality is for demonstration only in this prototype.")
        
        agree_to_terms = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy*",
            value=st.session_state.signup_data.get("agree_to_terms", False)
        )
        
        submitted = st.form_submit_button(
            "Create Account",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            # Validate required fields
            required_fields = []
            
            if signup_type == "User":
                if not name: required_fields.append("Full Name")
                if not email: required_fields.append("Email")
                if not password: required_fields.append("Password")
            else:
                if not org_name: required_fields.append("Organization Name")
                if not email: required_fields.append("Email")
                if not password: required_fields.append("Password")
                if not address: required_fields.append("Organization Address")
                if not phone: required_fields.append("Contact Phone")
                if not gov_id_number: required_fields.append("Government ID Number")
            
            if not agree_to_terms:
                st.error("You must agree to the Terms of Service and Privacy Policy")
            elif required_fields:
                st.error(f"Please fill in all required fields: {', '.join(required_fields)}")
            else:
                # Save form data to session
                form_data = {
                    "name" if signup_type == "User" else "org_name": name if signup_type == "User" else org_name,
                    "email": email,
                    "address": address,
                    "phone": phone,
                    "agree_to_terms": agree_to_terms
                }
                
                if signup_type == "Organization":
                    form_data.update({
                        "description": description,
                        "gov_id_number": gov_id_number
                    })
                
                st.session_state.signup_data = form_data
                
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    if signup_type == "User":
                        cursor.execute("""
                            INSERT INTO users (name, email, password, address, phone)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (name, email, password, address, phone))
                        success_message = "User account created successfully!"
                    else:
                        cursor.execute("""
                            INSERT INTO organizations 
                            (org_name, email, password, description, address, phone, gov_id_type, gov_id_number)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (org_name, email, password, description, address, phone, gov_id_type, gov_id_number))
                        success_message = """Organization account created successfully! 
                                          Your account will be activated after verification."""
                    
                    conn.commit()
                    conn.close()
                    
                    st.session_state.signup_success = True
                    st.session_state.success_message = success_message
                    st.rerun()  # This will refresh the page and show the success state
                    
                except Exception as e:
                    if "email" in str(e).lower():
                        st.error("This email is already registered. Please use a different email.")
                    else:
                        st.error(f"An error occurred: {str(e)}")

# Show success message if we've had a successful submission
else:
    st.success(st.session_state.success_message)
    st.balloons()
    
    if st.button("Go to Login Page", type="primary"):
        st.switch_page("pages/2_Login.py")  # Assuming you have a login page
    
    if st.button("Create Another Account"):
        st.session_state.signup_success = False
        st.session_state.signup_data = {}
        st.rerun()

# Add footer links
st.divider()
st.caption("Already have an account? [Login here](login.py)")
st.caption("By creating an account, you agree to our Terms of Service and Privacy Policy")
