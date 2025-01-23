from builtins import Exception
import streamlit as st
from pathlib import Path
from tempfile import NamedTemporaryFile
import subprocess
import os
import video_processing  # Importing the backend processing script

# Title of the Streamlit app
st.title("Video Processing App")

# Upload video file through the app
uploaded_file = st.file_uploader("Upload a video (.wmv)", type=["wmv"])

if uploaded_file is not None:
    st.write("Processing video...")

    # Save the uploaded file to a temporary file
    with NamedTemporaryFile(delete=False, suffix=".wmv") as temp_file:
        temp_file.write(uploaded_file.read())
        input_path = temp_file.name

    # Call the backend processing function
    try:
        output_path = video_processing.process_video(input_path)
        st.write(f"Video processed successfully! Displaying processed video.")
        st.video(output_path)  # Display the processed video
    except Exception as e:
        st.write(f"An error occurred during video processing: {str(e)}")
