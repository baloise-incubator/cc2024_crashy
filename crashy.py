"""Program to play with image LLMs."""

import base64
import datetime
from pathlib import Path

import streamlit as st
from openai import OpenAI

from exif import ExifData
from llm import call_llm, call_transcription
from model import DamageReport

client = OpenAI()
st.title("Crashy App")


def check_damage_report(final_resp: DamageReport) -> dict[str, bool]:
    """Check all conditions and return a dictionary of problems."""
    return {
        "car_not_visible": not all(final_resp.vehicle_present),
        "no_damage": not final_resp.damage_recognized,
        "multiple_vehicles": final_resp.number_of_unique_vehicles > 1,
        "damage_not_visible": not final_resp.damage_fully_visible,
        "fire_present": final_resp.is_fire_present,
    }


def audio_input() -> str | None:
    """Capture audio input and return its transcription."""
    audio_value = st.experimental_audio_input("Was ist passiert?")
    if audio_value:
        return call_transcription(audio_value.read())

    return None


transcription = audio_input()
st.write(transcription)

if transcription:
    speech_file_path = Path(__file__).parent / "audio" / "speech.mp3"
    with speech_file_path.open("rb") as f:
        st.audio(f, format="audio/mp3", autoplay=True)

    uploaded_file = st.file_uploader(
        "Bitte laden Sie ein " "Bild vom Schaden hoch",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

    if uploaded_file:
        if "damages" in st.session_state:
            del st.session_state["damages"]
        with st.spinner("Analysiere Bilder..."):
            n_cols = min(4, len(uploaded_file))
            cols = st.columns(n_cols)
            for i in range(len(uploaded_file)):
                cols[i % n_cols].image(
                    uploaded_file[i], caption=f"Foto Nr. {i+1}", use_column_width=True
                )

            # Function to encode the image
            def encode_image(data: list[bytes]) -> list[str]:
                """Encode the given image."""
                return [base64.b64encode(img).decode("utf-8") for img in data]

            images = [file.getvalue() for file in uploaded_file]
            base64_images = encode_image(images)
            img_content = []
            for base64_image in base64_images:
                content = {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
                img_content.append(content)

            final_resp = call_llm(transcription, base64_images)
            exif = ExifData(images)

            if exif.creation_times:
                try:
                    first_valid_time = next(
                        time for time in exif.creation_times if time
                    )
                    dt = datetime.datetime.strptime(
                        first_valid_time, "%Y:%m:%d %H:%M:%S"
                    ).replace(tzinfo=datetime.timezone.utc)
                except StopIteration:
                    dt = None

            map_data = (
                {
                    "latitude": [ex[0] for ex in exif.locations if ex],
                    "longitude": [ex[1] for ex in exif.locations if ex],
                }
                if exif.locations
                else None
            )

        st.write(final_resp)
        if not final_resp:
            st.write(
                "Das Bild konnte leider nicht analysiert werden. "
                "Bitte laden Sie ein neues Bild hoch"
            )
        if final_resp:
            problems = check_damage_report(final_resp)

            error_messages = {
                "car_not_visible": "Auf mindestens einem Bild ist das Auto nicht sichtbar. "
                "Bitte laden Sie ein Bild vom gesamten Fahrzeug hoch. Betroffene Bilder:"
                f"{', '.join([f'Bild Nr {i+1!s}' for i, visible in
                enumerate(final_resp.vehicle_present) if not visible])}",
                "no_damage": "Es wurde kein Schaden erkannt. Bitte laden Sie ein "
                "Bild mit sichtbarem Schaden hoch.",
                "multiple_vehicles": "Mehrere Fahrzeuge auf dem Bild. "
                "Bitte laden Sie Bilder nur von einem Fahrzeug hoch.",
                "damage_not_visible": "Der Schaden ist nicht vollständig sichtbar. "
                "Bitte laden Sie ein Bild mit vollständig sichtbarem Schaden hoch.",
            }

            # Check if any problems exist
            active_problems = [
                msg for problem, msg in error_messages.items() if problems[problem]
            ]

            if active_problems:
                for message in active_problems:
                    st.warning(message)

            if final_resp.is_fire_present:
                st.warning("Brandgefahr! Bitte entfernen Sie sich vom Fahrzeug.")

            st.write("Schadensbericht:")

            @st.fragment
            def fill_out_form() -> None:
                """Fill out the damage report form."""
                if "damages" not in st.session_state:
                    st.session_state.damages = (
                        final_resp.detailed_damage_description.copy()
                    )
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Kennzeichen", final_resp.license_plate_number)

                    st.write("### Aktuelle Schäden")
                    for idx, damage in enumerate(st.session_state.damages):
                        st.checkbox(damage, value=True, key=f"damage_{idx}")

                    new_damage = st.text_input("Fügen Sie zusätzliche Schäden hinzu")

                    try:
                        if new_damage and new_damage not in st.session_state.damages:
                            st.session_state.damages.append(new_damage)
                            st.toast(f"Schaden '{new_damage}' hinzugefügt.")
                            new_damage = ""
                            st.rerun(scope="fragment")

                    except ValueError as e:
                        st.exception(e)
                        st.error("Schaden konnte nicht hinzugefügt werden.")
                with col2:
                    if dt:
                        st.date_input("Datum", dt.date())
                        st.time_input("Uhrzeit", dt.time())
                    if map_data:
                        st.map(map_data)

                st.write("Bitte überprüfen Sie die Angaben.")
                if st.button("Schaden melden"):
                    ...

            fill_out_form()
