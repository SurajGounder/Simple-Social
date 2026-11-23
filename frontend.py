import os
import streamlit as st
import requests
import base64
import urllib.parse

st.set_page_config(page_title="Simple Social", layout="wide")

API_URL = os.getenv("API_URL", "http://localhost:8000")


# --------------------------------------------------
# Initialize Session State
# --------------------------------------------------

if "token" not in st.session_state:
    st.session_state.token = None

if "user" not in st.session_state:
    st.session_state.user = None


# --------------------------------------------------
# Authorization Headers
# --------------------------------------------------

def get_headers():
    """Get authorization headers with token"""

    if st.session_state.token:
        return {
            "Authorization": f"Bearer {st.session_state.token}"
        }

    return {}


# --------------------------------------------------
# Login Page
# --------------------------------------------------

def login_page():

    st.title("🚀 Welcome to Simple Social")

    email = st.text_input("Email:")

    password = st.text_input(
        "Password:",
        type="password"
    )

    if email and password:

        col1, col2 = st.columns(2)

        # LOGIN
        with col1:

            if st.button(
                "Login",
                type="primary",
                use_container_width=True
            ):

                login_data = {
                    "username": email,
                    "password": password
                }

                try:

                    response = requests.post(
                        f"{API_URL}/auth/jwt/login",
                        data=login_data
                    )

                    if response.status_code == 200:

                        token_data = response.json()

                        st.session_state.token = token_data["access_token"]

                        # Get user information
                        user_response = requests.get(
                            f"{API_URL}/users/me",
                            headers=get_headers()
                        )

                        if user_response.status_code == 200:

                            st.session_state.user = user_response.json()

                            st.success("Login successful!")

                            st.rerun()

                        else:

                            st.session_state.token = None

                            st.error("Failed to retrieve user information.")

                    else:

                        st.error("Invalid email or password!")

                except requests.RequestException as e:

                    st.error(f"Connection error: {e}")

        # SIGNUP
        with col2:

            if st.button(
                "Sign Up",
                type="secondary",
                use_container_width=True
            ):

                signup_data = {
                    "email": email,
                    "password": password
                }

                try:

                    response = requests.post(
                        f"{API_URL}/auth/register",
                        json=signup_data
                    )
                    if response.status_code == 201:

                        st.success(
                            "Account created successfully! Click Login now."
                        )

                    else:

                        try:
                            error_detail = response.json().get(
                                "detail",
                                "Registration failed"
                            )
                        except ValueError:
                            error_detail = response.text

                        st.error(f"Registration failed: {error_detail}")

                except requests.RequestException as e:

                    st.error(f"Connection error: {e}")

    else:

        st.info("Enter your email and password above.")


# --------------------------------------------------
# Upload Page
# --------------------------------------------------

def upload_page():

    st.title("📸 Share Something")

    uploaded_file = st.file_uploader(
        "Choose media",
        type=[
            "png",
            "jpg",
            "jpeg",
            "mp4",
            "avi",
            "mov",
            "mkv",
            "webm"
        ]
    )

    caption = st.text_area(
        "Caption:",
        placeholder="What's on your mind?"
    )

    if uploaded_file and st.button(
        "Share",
        type="primary"
    ):

        with st.spinner("Uploading..."):

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                )
            }

            data = {
                "caption": caption
            }

            try:

                response = requests.post(
                    f"{API_URL}/upload",
                    files=files,
                    data=data,
                    headers=get_headers()
                )

                if response.status_code == 200:

                    st.success("Posted successfully!")

                    st.rerun()

                else:

                    st.error("Upload failed!")

                    st.write(response.text)

            except requests.RequestException as e:

                st.error(f"Upload connection error: {e}")


# --------------------------------------------------
# ImageKit Text Overlay
# --------------------------------------------------

def encode_text_for_overlay(text):

    """Encode text for ImageKit overlay"""

    if not text:
        return ""

    base64_text = base64.b64encode(
        text.encode("utf-8")
    ).decode("utf-8")

    return urllib.parse.quote(base64_text)


# --------------------------------------------------
# ImageKit Transformation URL
# --------------------------------------------------

def create_transformed_url(
    original_url,
    transformation_params,
    caption=None
):

    if caption:

        encoded_caption = encode_text_for_overlay(caption)

        text_overlay = (
            f"l-text,ie-{encoded_caption},"
            "ly-N20,lx-20,fs-100,"
            "co-white,bg-000000A0,l-end"
        )

        transformation_params = text_overlay

    if not transformation_params:

        return original_url

    parts = original_url.split("/")

    base_url = "/".join(parts[:4])

    file_path = "/".join(parts[4:])

    return (
        f"{base_url}/tr:{transformation_params}/{file_path}"
    )


# --------------------------------------------------
# Feed Page
# --------------------------------------------------

def feed_page():

    st.title("🏠 Feed")

    try:

        response = requests.get(
            f"{API_URL}/feed",
            headers=get_headers()
        )

        # Check API response status
        if response.status_code != 200:

            st.error(
                f"Failed to load feed. "
                f"Status Code: {response.status_code}"
            )

            st.write(response.text)

            return

        # Parse JSON response
        try:

            data = response.json()

        except ValueError:

            st.error("FastAPI returned an invalid JSON response.")

            st.write(response.text)

            return

        # Validate response
        if not isinstance(data, dict):

            st.error(
                "Unexpected API response. Expected a JSON object "
                "containing posts."
            )

            st.write(data)

            return

        posts = data.get("posts", [])

        if not isinstance(posts, list):

            st.error("Invalid posts data received from API.")

            return

        # Display empty feed message
        if not posts:

            st.info(
                "No posts yet! Be the first to share something."
            )

            return

        # Display posts
        for post in posts:

            st.markdown("---")

            # Post Header
            col1, col2 = st.columns([4, 1])

            with col1:

                st.markdown(
                    f"**{post.get('email', 'Unknown')}** "
                    f"• {post.get('created_at', '')[:10]}"
                )

            # Delete Button
            with col2:

                if post.get("is_owner", False):

                    if st.button(
                        "🗑️",
                        key=f"delete_{post['id']}",
                        help="Delete post"
                    ):

                        try:

                            response = requests.delete(
                                f"{API_URL}/posts/{post['id']}",
                                headers=get_headers()
                            )

                            if response.status_code == 200:

                                st.success("Post deleted!")

                                st.rerun()

                            else:

                                st.error("Failed to delete post!")

                                st.write(response.text)

                        except requests.RequestException as e:

                            st.error(f"Delete error: {e}")

            # Post Caption
            caption = post.get("caption", "")

            # Display Image
            if post.get("file_type") == "image":

                image_url = create_transformed_url(
                    post["url"],
                    "",
                    caption
                )

                st.image(
                    image_url,
                    width=300
                )

            # Display Video
            elif post.get("file_type") == "video":

                video_url = create_transformed_url(
                    post["url"],
                    "w-400,h-200,cm-pad_resize,bg-blurred"
                )

                st.video(
                    video_url,
                    width=300
                )

                st.caption(caption)

            else:

                st.warning("Unsupported media type.")

            st.markdown("")


    except requests.RequestException as e:

        st.error(f"Unable to connect to FastAPI: {e}")


# --------------------------------------------------
# Main Application
# --------------------------------------------------

if st.session_state.user is None:

    login_page()

else:

    # Sidebar
    st.sidebar.title(
        f"👋 Hi {st.session_state.user['email']}!"
    )

    # Logout
    if st.sidebar.button("Logout"):

        st.session_state.user = None

        st.session_state.token = None

        st.rerun()

    st.sidebar.markdown("---")

    # Navigation
    page = st.sidebar.radio(
        "Navigate:",
        [
            "🏠 Feed",
            "📸 Upload"
        ]
    )

    if page == "🏠 Feed":

        feed_page()

    else:

        upload_page()