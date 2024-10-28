"""Program to play with image LLMs."""

import base64
from typing import Optional

import streamlit as st
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()
st.title("Crashy App")


class AccidentReport(BaseModel):
    """An accident report model."""

    car_present: bool
    damage_recognized: bool
    damage_fully_visible: bool
    damage_severity: str  # 'low', 'medium', 'high'
    damage_location: str  # z.B. 'Front', 'Heck', 'Seiten', 'Dach'
    fire_present: bool
    license_plate_number: Optional[str]  # noqa: UP007
    detailed_damage_description: str


prompt = """
Sie sind ein hilfreicher Assistent für Autounfälle namens "crashy". Ihre Aufgabe ist es, einen umfassenden Schadensbericht basierend auf den bereitgestellten Fahrzeugbildern zu erstellen. Nutzen Sie alle bereitgestellten Bilder und fordern Sie bei Bedarf zusätzliche Bilder oder Details an, um eine genaue Bewertung vornehmen zu können. Beschreiben Sie ausschließlich die sichtbaren Schäden auf den Bildern und vermeiden Sie es, zusätzliche Informationen einzubeziehen.

Folgende Angaben müssen im Bericht enthalten sein:

1. **Fahrzeug vorhanden**:
   - Bestätigen Sie, dass das Fahrzeug auf den Bildern vollständig sichtbar ist.
   - **Erforderlich**: Ja

2. **Erkannter Schaden**:
   - Bestätigen Sie, dass Schäden am Fahrzeug erkennbar sind.
   - **Erforderlich**: Ja

3. **Vollständige Sichtbarkeit des Schadens**:
   - Bestätigen Sie, dass der Schaden vollständig auf den Bildern sichtbar ist.
   - **Erforderlich**: Ja

4. **Schweregrad des Schadens**:
   - Bewerten Sie den Schaden als niedrig, mittel oder hoch.
   - **Erforderlich**: Ja

5. **Schadensort am Fahrzeug**:
   - Geben Sie an, wo sich der Schaden am Fahrzeug befindet (z.B. Front, Heck, Seiten, Dach).
   - **Erforderlich**: Ja

6. **Brandgefahr**:
   - Bestätigen Sie, ob Anzeichen von Brand vorhanden sind (Ja/Nein).
   - **Erforderlich**: Ja

7. **Kennzeichen**:
   - Erfassen Sie das Kennzeichen nur, wenn es klar lesbar und vollständig erkennbar ist.
   - Wenn das Kennzeichen nicht zu 100% sichtbar ist, geben Sie `None` an.

8. **Zusätzliche Details**:
   - Fügen Sie eine detaillierte Beschreibung der sichtbaren Schäden hinzu, einschließlich der betroffenen Fahrzeugteile und der Art des Schadens (z.B. Dellen, Kratzer, gebrochene Spiegel).

**Ausgabeformat**:
Nutzen Sie das folgende Pydantic-Modell, um Ihre Antwort zu strukturieren:

```python
from pydantic import BaseModel
from typing import Optional

class AccidentReport(BaseModel):
    car_present: bool
    damage_recognized: bool
    damage_fully_visible: bool
    damage_severity: str  # 'low', 'medium', 'high'
    damage_location: str  # z.B. 'Front', 'Heck', 'Seiten', 'Dach'
    fire_present: bool
    license_plate_number: Optional[str]
    detailed_damage_description: str

{
    "car_present": true,
    "damage_recognized": true,
    "damage_fully_visible": true,
    "damage_severity": "medium",
    "damage_location": "Front",
    "fire_present": false,
    "license_plate_number": "AB123CD",
    "detailed_damage_description": "Die Frontstoßstange ist stark verbeult, der vordere Stoßfänger ist gebrochen und der Motorraum weist Anzeichen von Ölverlust auf."
}

"""  # noqa: E501


uploaded_file = st.file_uploader(
    "Bitte laden Sie ein " "Bild vom Schaden hoch", type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    st.image(uploaded_file, caption="Uploaded Image.", use_column_width=True)
    st.write("")
    st.write("Analyisere...")

    # Function to encode the image
    def encode_image(data: bytes) -> str:
        """Encode the given image."""
        return base64.b64encode(data).decode("utf-8")

    base64_image = encode_image(uploaded_file.getvalue())

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
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            },
        ],
        response_format=AccidentReport,
        temperature=0.1,
    )

    st.write(response.choices[0].message.parsed)
    final_resp = response.choices[0].message.parsed
    if not final_resp:
        st.write(
            "Das Bild konnte leider nicht analysiert werden. "
            "Bitte laden Sie ein Bild vom gesamten Fahrzeug hoch."
        )
    else:
        if not final_resp.car_present:
            st.write(
                "Das Auto ist nicht sichtbar. "
                "Bitte laden Sie ein Bild vom gesamten Fahrzeug hoch."
            )
        if not final_resp.damage_recognized:
            st.write(
                "Kein Schaden erkannt. "
                "Bitte laden Sie ein Bild mit sichtbarem Schaden hoch."
            )
        if not final_resp.damage_fully_visible:
            st.write(
                "Schaden nicht vollständig sichtbar. "
                "Bitte laden Sie ein Bild mit vollständig sichtbarem Schaden hoch."
            )
        if final_resp.fire_present:
            st.warning("Brandgefahr!")
        if final_resp.damage_severity == "high":
            st.warning("Hoher Schaden!")
