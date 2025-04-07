import streamlit as st
import moviepy.editor as mp
import whisper
import cv2
import tempfile
import os
import ffmpeg
import numpy as np

st.title("🎬 Viral Shorts Generator (by Ken & AI)")

uploaded_file = st.file_uploader("Upload a video", type=["mp4", "mov", "avi"])
if uploaded_file is not None:
    with st.spinner("Processing..."):
        # Save uploaded file
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        # Load video and cut 30 seconds
        video = mp.VideoFileClip(input_path)
        clip = video.subclip(0, min(30, video.duration))
        short_path = os.path.join(temp_dir, "short.mp4")
        clip.write_videofile(short_path)

        # Transcribe with Whisper
        model = whisper.load_model("base")
        result = model.transcribe(short_path)
        transcript = result["text"]

        # Wrap transcript into lines
        def wrap_text(text, max_width_chars=50):
            words = text.split()
            lines = []
            line = ''
            for word in words:
                if len(line + ' ' + word) < max_width_chars:
                    line += ' ' + word
                else:
                    lines.append(line.strip())
                    line = word
            lines.append(line.strip())
            return lines

        wrapped_lines = wrap_text(transcript)

        # Add subtitles using OpenCV
        cap = cv2.VideoCapture(short_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        output_avi = os.path.join(temp_dir, "output.avi")
        out = cv2.VideoWriter(output_avi, cv2.VideoWriter_fourcc(*'XVID'), fps, (width, height))

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_thickness = 2
        line_height = 30
        y_start = height - (line_height * len(wrapped_lines)) - 20

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            for i, line in enumerate(wrapped_lines):
                y = y_start + i * line_height
                cv2.putText(frame, line, (40, y), font, font_scale, (255,255,255), font_thickness, cv2.LINE_AA)
            out.write(frame)

        cap.release()
        out.release()

        # Convert to mp4
        final_path = os.path.join(temp_dir, "viral_short.mp4")
        ffmpeg.input(output_avi).output(final_path, vcodec='libx264', acodec='aac').run()

        with open(final_path, "rb") as file:
            st.download_button(label="📥 Download Your Viral Short", data=file, file_name="viral_short.mp4")

        st.success("✅ Done! Share your short everywhere.")
