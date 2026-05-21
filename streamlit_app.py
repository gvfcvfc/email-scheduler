import streamlit as st

verify_email_page = st.Page(
    "pages/verify_email.py",
    title="Verify Email",
    url_path="verify-email",
)

reset_password_page = st.Page(
    "pages/reset_password.py",
    title="Reset Password",
    url_path="reset-password",
)

pg = st.navigation([
    verify_email_page,
    reset_password_page,
])

pg.run()
