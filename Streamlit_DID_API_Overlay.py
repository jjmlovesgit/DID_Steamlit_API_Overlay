import fileinput
import streamlit as st
import requests
import json
import base64
import random
import string
from datetime import datetime
import os
from typing import Dict
from config import API_KEY

# Provide the path to your logo image file
logo = "https://th.bing.com/th/id/OIG.4dx5A44rg1JYp6kqsJO5?w=270&h=270&c=6&r=0&o=5&pid=ImgGng"

st.sidebar.markdown(
    """
    <img src="{}" style="width:250px;height:250px;">
    """.format(logo),
    unsafe_allow_html=True,
)

def get_did_credits() -> Dict[str, str]:
    # D-ID Credit balance
    url = "https://api.d-id.com/credits"
    auth_string = f"{API_KEY}:"
    base64_auth_string = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "accept": "application/json",
        "Authorization": f"Basic {base64_auth_string}"
    }
    response = requests.get(url, headers=headers)
    return json.loads(response.text)

def write_config_file(api_key: str) -> str:
    if len(api_key) == 0:
        return "Please provide a valid API key"
    with open("config.py", "w") as f:
        f.write(f'API_KEY = "{api_key}"')
    file_path = os.path.abspath("config.py")
    return f"Config file saved as {file_path}"

def create_did_talk(script: str, source_url: str, voice_id: str) -> Dict[str, str]:
    # D-ID Text based talk crreation
    url = "https://api.d-id.com/talks"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {API_KEY}"
    }
    payload = {
        "source_url": source_url,
        "script": {
            "type": "text",
            "input": script,
            "provider": {
                "type": "microsoft",
                "voice_id": voice_id,
                "voice_config": {
                    "style": "Default"
                }
            }
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response_json = json.loads(response.text)
    talk_id = response_json["id"]
    status = response_json["status"]
    return talk_id, status

def validate_input(script, source_url, voice_id):
    # Script must be a test input and not blank
    if not script:
        raise ValueError("Script must not be blank")
    if not source_url:
        raise ValueError("Source URL must not be blank")
    return True

def get_did_talk(talk_id: str) -> str:
    # D-ID Talk ID lookup to retrieve Video Link
    if talk_id.strip() == "":
        return "Invalid talk ID. Please try again."
    url = f"https://api.d-id.com/talks/{talk_id}"
    auth_string = f"{API_KEY}:"
    base64_auth_string = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "accept": "application/json",
        "Authorization": f"Basic {base64_auth_string}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 404:
        return f"Talk ID '{talk_id}' not found. Please try again."
    response_json = json.loads(response.text)
    result_url = response_json["result_url"]
    return result_url

def download_video(url: str) -> str:
    # Check if the url is valid
    if not url:
        return "Please enter a valid URL."
    # Create directory if it does not exist
    if not os.path.exists("demo_videos"):
        os.makedirs("demo_videos")
    # Create a unique file name with random characters and current timestamp
    file_name = os.path.join("demo_videos", ''.join(random.choices(string.ascii_lowercase, k=5)) + '_' + datetime.now().strftime("%Y%m%d%H%M%S") + ".mp4")
    # Download the video and save it to the file
    response = requests.get(url, stream=True)
    with open(file_name, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            f.write(chunk)
    # Return the full file path of the downloaded video
    return file_name

def main():
    # Streamlit sidebar
    st.sidebar.title("D-ID API Workflow")
    selection = st.sidebar.radio("Go to", ["Home", "Write API Config File", "Create Video", "Get Talk", "Download Video", "Play Local Video"])
    if st.sidebar.button('Get Credits'):
        credits = get_did_credits()['remaining']
        st.sidebar.markdown(f"## Credits Remaining: {credits}")

    if selection == "Home":
        st.title("D-ID Labs API Demo")
        st.markdown("""
            Welcome to the D-ID Labs API Demo! This application allows you to interact with the D-ID API
            to perform various tasks related to video creation and retrieval. Please use the sidebar on the
            left to navigate and select a task.

            - **Write API Config File**: Write your API Key to Config.py to use this workflow (Or do it manually).
            - **Create Video**: Create a D-ID talk by providing a script, source URL, and voice ID.
            - **Get Talk**: Retrieve the result URL of a previously created D-ID talk by providing its talk ID.
            - **Download Video**: Download a video from a provided URL and save it locally.
            - **Play Local Video**: Upload and play a local .mp4 video file.

            Check the remaining API credits in the sidebar to ensure you have sufficient credits for your tasks.
        """)

    elif selection == "Write API Config File":
        st.title("Write API Config File")
        api_key_input = st.text_input("Use whenever you rotate your API key", type="password", value="", key="api_key_input", autocomplete="off")
        if st.button('Save Config'):
            status = write_config_file(api_key_input)
            st.write("Status: ", status)

    elif selection == "Create Video":
        st.title("Create Video")
        script_input = st.text_area("Script")
        source_url_input = st.text_input("Source URL")
        voice_id_input = st.text_input("Voice ID", "en-US-ChristopherNeural")
        if st.button('Create Video'):
            validate_input(script_input, source_url_input, voice_id_input) 
            talk_id, status = create_did_talk(script_input, source_url_input, voice_id_input)
            st.write("Talk ID: ", talk_id)
            st.write("Status: ", status)

    elif selection == "Get Talk":
        st.title("Get Talk")
        talk_id = st.text_input("Talk ID")
        if st.button('Get Talk'):
            result_url = get_did_talk(talk_id)
            st.write("Result URL: ", result_url)

    elif selection == "Download Video":
        st.title("Download Video")
        video_url = st.text_input("Video URL")
        if st.button('Download Video'):
            filepath = download_video(video_url)
            st.markdown(f"### Download Status: Video downloaded successfully.")
            st.markdown(f"### Full File Path: {os.path.abspath(filepath)}")
            st.markdown(f"### Use the 'Play Local Video' option to play it") 

    elif selection == "Play Local Video":
        st.title("Play Local Video")
        video_file = st.sidebar.file_uploader("Upload a video", type=['mp4'], accept_multiple_files=False)
        if video_file is not None:
            st.video(video_file)

if __name__ == "__main__":
    main()
