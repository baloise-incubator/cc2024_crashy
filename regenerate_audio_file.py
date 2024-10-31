"""Program to generate the audio files."""
from pathlib import Path

from openai import OpenAI

client = OpenAI()

speech_file_path = Path(__file__).parent / "audio" / "speech.mp3"
response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Viele Dank für die Audioeingabe. "
          "Bitte laden Sie nun ein Bild vom Schaden hoch.",
)
