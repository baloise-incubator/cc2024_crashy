"""Module to manage LLM calls."""


import base64

from openai import OpenAI
from openai.types.chat.parsed_chat_completion import ContentType

from model import DamageReport
from prompt import prompt

client = OpenAI()


def call_transcription(audio_file: bytes) -> str:
    """Call the transcription API with the audio file."""
    encoded_string = base64.b64encode(audio_file).decode("utf-8")

    completion = client.chat.completions.create(
        model="gpt-4o-audio-preview",
        modalities=["text"],
        audio={"voice": "alloy", "format": "wav"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What is in this recording?"
                    },
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": encoded_string,
                            "format": "wav"
                        }
                    }
                ]
            },
        ]
    )
    return completion.choices[0].message.content


def call_llm(audio_transcript: str, base64_images: list[str]) -> ContentType | None:
    """Call the LLM  with the list of images."""
    user_input = [{"type": "text", "text": audio_transcript}]
    for base64_image in base64_images:
        content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
        }
        user_input.append(content)

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            },
            {
                "role": "user",
                "content": user_input,
            },
        ],
        response_format=DamageReport,
        temperature=0.1,
    )
    return response.choices[0].message.parsed
