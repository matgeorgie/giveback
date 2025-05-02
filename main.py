import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="GiveBack",
    page_icon="🎁",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom styling with native Streamlit options
st.markdown("""
    <style>
        .big-font {
            font-size:22px !important;
        }
        .feature-card {
            padding: 1.5rem;
            border-radius: 10px;
            background: rgba(240, 242, 246, 0.6);
            margin-bottom: 1rem;
        }
        .testimonial-card {
            padding: 1.5rem;
            border-radius: 10px;
            background: rgba(173, 216, 230, 0.2);
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# Hero Section
st.title("🎁 Welcome to GiveBack")
st.markdown("""
<span class="big-font">
GiveBack is a platform connecting generous donors to trusted organizations and individuals in need.
Sign up today to make a difference!
</span>
""", unsafe_allow_html=True)

# Metrics Counter (simulated)
st.markdown("---")
st.subheader("🌍 Our Collective Impact")
col1, col2, col3 = st.columns(3)
col1.metric("Donations Made", "1,245,678", "+12,345 this week")
col2.metric("Organizations Supported", "4,321", "+42 this month")
col3.metric("Countries Reached", "127", "6 new this year")

# Features Section
st.markdown("---")
st.header("✨ Why Choose GiveBack?")

features = [
    ("🔒", "Trust & Transparency", "Every donation is tracked and verified, ensuring your generosity reaches those who need it most."),
    ("🌍", "Global Impact", "Connect with causes worldwide and make a difference in communities across the globe."),
    ("💝", "Easy Giving", "Simple, secure, and efficient donation process that takes just minutes to complete with ease."),
    ("📊", "Real Tracking", "See exactly how your contributions are being used with detailed impact reports."),
    ("🤝", "Community Building", "Join a network of like-minded individuals committed to making positive change."),
    ("🏆", "Verified Partners", "All organizations undergo rigorous vetting to ensure legitimacy and effectiveness.")
]

cols = st.columns(3)
for i, (emoji, title, desc) in enumerate(features):
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(f"### {emoji} {title}")
            st.markdown(desc)

# How It Works Section
st.markdown("---")
st.header("📝 How It Works")

steps = [
    ("1️⃣", "Create Account", "Sign up in less than 2 minutes as a donor or organization"),
    ("2️⃣", "Browse Causes", "Discover verified organizations and individuals in need"),
    ("3️⃣", "Make a Donation", "Give securely with multiple payment options"),
    ("4️⃣", "Track Impact", "Receive updates on how your contribution made a difference")
]

for emoji, title, desc in steps:
    with st.expander(f"{emoji} {title}"):
        st.markdown(desc)
        if title == "Create Account":
            if st.button("Start Now", key=f"btn_{title}"):
                st.switch_page("pages/1_Sign_Up.py")

# Testimonials Section
st.markdown("---")
st.header("💬 Voices of Change")

testimonials = [
    ("🌟", "Sarah K.", "Donor since 2022", "GiveBack has made donating so easy and transparent. I can see exactly where my money goes!"),
    ("💫", "Michael T.", "Monthly Contributor", "The platform connected me with amazing causes I never would have found otherwise."),
    ("✨", "Hope Foundation", "Non-profit Partner", "As a small non-profit, GiveBack has helped us reach more donors than ever before."),
    ("🏆", "David & Priya", "Corporate Donors", "Our employee matching program through GiveBack has boosted team morale and impact.")
]

for emoji, name, role, quote in testimonials:
    with st.container(border=True):
        col1, col2 = st.columns([1, 10])
        with col1:
            st.markdown(f"### {emoji}")
        with col2:
            st.markdown(f"**{name}**  \n*{role}*")
            st.markdown(f"> {quote}")

# Call to Action
st.markdown("---")
st.header("🚀 Ready to Make an Impact?")
st.markdown("Join thousands of others who are transforming lives every day")

cta_col1, cta_col2 = st.columns([3, 2])
with cta_col1:
    st.markdown("""
    - Create your free account in minutes
    - No obligation - give when you can
    - 100% of donations reach recipients (we cover fees)
    """)
with cta_col2:
    if st.button("Sign Up Now", type="primary", use_container_width=True):
        st.switch_page("pages/1_Sign_Up.py")
    if st.button("Contact Us", use_container_width=True):
        st.page_link("pages/6_Contact_Us.py") 

# Footer
st.markdown("---")
st.markdown("© 2024 GiveBack | Making the world a better place, one donation at a time")