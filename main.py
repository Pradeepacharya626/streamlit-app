import streamlit as st
import cv2
import numpy as np
import requests
import time

if 'show_camera' not in st.session_state:
    st.session_state.show_camera = True

# taken randomly
st.session_state["photo"] = "good"

def update_percentage():
    """
    This function calculates and returns the percentage of proper posture.
    """
    global total_count, proper_count  # Use global variables
    if total_count > 0:
        percentage_proper = (proper_count / total_count) * 100
        st.session_state.last_percentage = percentage_proper  # Store the last percentage in session state
        return percentage_proper
    else:
        return None


def process_posture(img_array, total_count, proper_count):
    """
    This function sends an image to the API, retrieves posture, and updates counts.
    """
    response = call_api(img_array)  # Call the API function (assumed to exist)
    if response and response.status_code == 200:
        result = response.json()  # Assuming API returns a JSON response
        posture = result.get("Posture",
                             "Unknown").upper()  # Extract and convert posture to uppercase
        total_count += 1
        if posture == "PROPER":
            proper_count += 1
        return posture, total_count, proper_count
    else:
        return None, total_count, proper_count


# Function to capture image and call API
def capture_image1(key):

    if st.session_state.show_camera == True :
        picture = st.camera_input("", key=key)  # Pass a unique key

    if picture:
        img_array = np.frombuffer(picture.getvalue(), dtype=np.uint8)

        # Resize the image
        target_width = 1280
        aspect_ratio = cv2.imdecode(img_array, cv2.IMREAD_COLOR).shape[1] / \
                       cv2.imdecode(img_array, cv2.IMREAD_COLOR).shape[0]
        if aspect_ratio > target_width / 720:  # Wider than desired aspect ratio
            new_height = 720
            new_width = int(new_height * aspect_ratio)
        else:  # Taller or equal to desired aspect ratio
            new_width = target_width
            new_height = int(new_width / aspect_ratio)
        resized_img = cv2.resize(cv2.imdecode(img_array, cv2.IMREAD_COLOR),
                                 (new_width, new_height))

        # Call the API with resized image
        api_url = 'https://13.127.229.205/upload'
        files = {'file': (
        'image.jpg', cv2.imencode(".jpg", resized_img)[1].tobytes(),
        'image/jpeg')}
        response = requests.post(api_url, files=files, verify=False)

        return response  # Return the API response object
    else:
        return None  # Return None if no picture is captured


def capture_image():
    st.session_state.show_camera = False
    if st.session_state["photo"] == "good" :
        st.experimental_rerun()
    cap = cv2.VideoCapture(0)  # Open the default camera (0)

    if not cap.isOpened():
        st.error("Error opening camera.")
        return None

    # Set the capture resolution to 1280x720
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    ret, frame = cap.read()  # Read a frame from the camera

    if not ret:
        st.error("Error capturing frame.")
        return None

    cap.release()  # Release the camera

    return frame  # Return the captured frame


# Function to call API
def call_api(img_array):
    # Call the API with the image
    api_url = 'https://13.127.229.205/upload'
    files = {'file': (
    'image.jpg', cv2.imencode(".jpg", img_array)[1].tobytes(), 'image/jpeg')}
    response = requests.post(api_url, files=files, verify=False)

    return response  # Return the API response object


if __name__ == "__main__":
    st.markdown("<h1 style='text-align: center;'>Welcome to SiTFiT</h1>",
                unsafe_allow_html=True)
    st.markdown(
        "<h4 style='text-align: center;'>Click to Check Your Posture</h4>",
        unsafe_allow_html=True)
    global proper_count
    global total_count
    proper_count = 0
    total_count = 0
    st.session_state.last_percentage = None  # Initialize session state for last percentage

    # Call the capture_image1 function with a unique key and get the response
    if st.session_state.show_camera == True :
        response = capture_image1("camera1")  # Use a unique key
    else :
        st.session_state["photo"] = "moderate"
        response = None

    if response:
        if response.status_code == 200:
            result = response.json()  # Assuming API returns a JSON response
            posture = result.get("Posture",
                                 "Unknown").upper()  # Extract and convert posture to uppercase

            if posture == "PROPER":
                st.success(
                    "You are in proper posture. You can start working now!")
            else:
                # Display message prompting the user to check posture
                st.warning(
                    "Please check your posture before proceeding. Make sure you sit straight.")
                st.error(
                    "You are not sitting in proper posture. Make sure you sit straight.")

            st.markdown(
                f"<div style='font-size: 24px; text-align: center; color: white;'>{posture} POSTURE</div>",
                unsafe_allow_html=True)
        else:
            st.error("Error occurred while calling the API.")

    frame = st.empty()
    captured_image = None
    streaming = False  # Flag to track streaming status
    percentage_text = st.empty()  # Text element to display percentage

    # Display both the "Start Capturing" and "Stop Capturing" buttons on the same level
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        start_button = st.button("Start Capturing", key="start_button")
    with col3:
        stop_button = st.button("Stop Capturing", key="stop_button")

    if start_button:
        streaming = True  # Set streaming flag to True when capturing starts

    while streaming:
        # Capture image if streaming flag is True
        captured_image = capture_image()
        if captured_image is not None:
            # Process the captured image
            response = call_api(captured_image)
            if response and response.status_code == 200:
                result = response.json()  # Assuming API returns a JSON response
                posture = result.get("Posture",
                                     "Unknown").upper()  # Extract and convert posture to uppercase
                st.markdown(
                    f"<div style='font-size: 24px; text-align: center; color: white;'>{posture} POSTURE</div>",
                    unsafe_allow_html=True)
                total_count += 1
                if posture == "PROPER":
                    proper_count += 1
            else:
                st.error("Error occurred while calling the API.")
        else:
            st.warning("No picture captured.")

        # Update the percentage display
        percentage = update_percentage()
        if percentage is not None:
            percentage_text.markdown(
                f"<div style='font-size: 32px; text-align: center; color: white;'><b>Percentage of proper posture: {percentage:.2f}%</b></div>",
                unsafe_allow_html=True)

        time.sleep(10)  # Capture image every 10 seconds

    if stop_button:
        streaming = False  # Set streaming flag to False when capturing stops
        st.warning("Capture stopped.")
        print("Total count", total_count)
        print("Proper count", proper_count)

st.session_state