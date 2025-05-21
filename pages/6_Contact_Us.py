import streamlit as st

st.title("Contact Us")

name = st.text_input("Your Name")
email = st.text_input("Your Email")
message = st.text_area("Your Message")

if st.button("Send Message"):
    if name and email and message:
        st.success("Thank you for contacting us! We will get back to you soon.")
    else:
        st.error("Please fill in all fields.")
