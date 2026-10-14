
import streamlit as st
import requests
import asyncio
import edge_tts
import os
from PIL import Image
from io import BytesIO
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

st.set_page_config(page_title="AI Shorts Generator", layout="wide")
st.title("AI YouTube Shorts Generator")

scenes = [
    {
        "narration": "Your brain is lying to you right now, and you don't even know it.",
        "prompt": "Glowing golden 3D human brain, dark cinematic background"
    },
    {
        "narration": "Here are three surprising things your brain does every day.",
        "prompt": "Human head silhouette with glowing neural networks, cinematic"
    },
    {
        "narration": "First, brain tissue itself has no pain receptors, even though your brain processes pain signals from your body.",
        "prompt": "Detailed human brain medical illustration, blue holographic lighting"
    },
    {
        "narration": "Second, your brain uses roughly twenty watts of power while you are awake and thinking.",
        "prompt": "Glowing lightbulb beside a luminous human brain, dark background"
    },
    {
        "narration": "Third, your brain helps stabilize your vision when your eyes move rapidly from one place to another.",
        "prompt": "Extreme close-up human eye reflecting a futuristic city"
    },
    {
        "narration": "Which fact surprised you most? Tell me in the comments!",
        "prompt": "Mysterious cinematic mirror in a dark room, blue neon lighting"
    }
]

voice = st.selectbox(
    "AI voice",
    ["en-US-AriaNeural", "en-US-GuyNeural",
     "en-US-ChristopherNeural", "en-GB-RyanNeural"]
)

st.info("Creates a narrated vertical video. Image generation requires internet access.")

def make_audio(text, path, selected_voice):
    async def run():
        tts = edge_tts.Communicate(
            text, selected_voice, rate="+10%"
        )
        await tts.save(path)
    asyncio.run(run())

def make_image(prompt, path):
    url = "https://image.pollinations.ai/prompt/" + requests.utils.quote(prompt)
    response = requests.get(
        url,
        params={"width": 720, "height": 1280, "nologo": "true"},
        timeout=120
    )
    response.raise_for_status()
    img = Image.open(BytesIO(response.content)).convert("RGB")
    img = img.resize((720, 1280))
    img.save(path, "JPEG", quality=90)

if st.button("Generate video"):
    os.makedirs("temp_assets", exist_ok=True)
    clips = []
    progress = st.progress(0)

    try:
        for i, scene in enumerate(scenes):
            st.write(f"Creating scene {i + 1} of {len(scenes)}")

            audio_path = f"temp_assets/audio_{i}.mp3"
            image_path = f"temp_assets/image_{i}.jpg"

            make_audio(scene["narration"], audio_path, voice)
            make_image(scene["prompt"], image_path)

            audio = AudioFileClip(audio_path)
            clip = ImageClip(image_path).set_duration(audio.duration)
            clip = clip.set_audio(audio)
            clips.append(clip)

            progress.progress((i + 1) / len(scenes))

        st.write("Rendering MP4...")
        final = concatenate_videoclips(clips, method="compose")
        output = "brain_facts_short.mp4"

        final.write_videofile(
            output,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            ffmpeg_params=["-pix_fmt", "yuv420p"]
        )

        final.close()
        for clip in clips:
            clip.close()

        st.success("Video created!")
        st.video(output)

        with open(output, "rb") as file:
            st.download_button(
                "Download your video",
                file,
                file_name=output,
                mime="video/mp4"
            )

    except Exception as error:
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        st.error(f"Generation failed: {error}")
        st.info("Try again later if an image or voice service is unavailable.")
