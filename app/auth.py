import streamlit as st
import hmac

def check_password():
    """Returns True if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        # Display the image in a centered column layout
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                """
                <h1 style="color: white; text-align: center; margin-bottom: 0;">Fly Me Away</h1>
                """,
                unsafe_allow_html=True
            )
            st.image("assets/logo.png", width=350)
            
            st.markdown(
                """
                <p style="color: white; text-align: center; margin-bottom: 0; font-size: 14px;">This is a pre-release version of the Fly Me Away app. This app is not monetized and does not collect any data from users. Please request access by sending an email to <a href="mailto:info@kineticequity.ch" style="color: #FFA500;">info@kineticequity.ch</a></p>
                """,
                unsafe_allow_html=True
            )
            
            # Add some space before the form
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.form("Credentials"):
                st.text_input("Username", key="username")
                st.text_input("Password", type="password", key="password")
                st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets["passwords"] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the username or password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False
