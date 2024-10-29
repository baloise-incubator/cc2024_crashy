"""Program to play with image LLMs."""

import base64
from typing import Optional

import streamlit as st
from openai import OpenAI
from pydantic import BaseModel


client = OpenAI()
st.title("Crashy App")

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum

class DamageSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class DamageLocation(str, Enum):
    front = "Front"
    rear = "Rear"
    sides = "Sides"
    roof = "Roof"

class VehicleDamage(BaseModel):
    fire_present: bool = Field(..., description="Indicates if there are signs of fire on the vehicle.")
    damage_severity: DamageSeverity = Field(..., description="Severity of the damage.")
    damage_location: DamageLocation = Field(..., description="Location of the damage on the vehicle.")
    license_plate_number: Optional[str] = Field(None, description="License plate number if fully visible.")
    detailed_damage_description: str = Field(..., description="Detailed description of the visible damages.")

    @validator('license_plate_number')
    def validate_license_plate(cls, v, values):
        if values.get('fire_present') and not v:
            raise ValueError("License plate number must be provided if there are signs of fire.")
        return v

class VehicleReport(BaseModel):
    vehicle_id: int = Field(..., description="Unique identifier for the vehicle.")
    damage: VehicleDamage

class AccidentReport(BaseModel):
    cars: List[VehicleReport] = Field(..., description="List of vehicles involved in the accident.")
    number_of_valid_images: int = Field(..., description="Number of valid images used for assessment.")
    number_of_unique_vehicles: int = Field(..., description="Number of unique vehicles visible in the images.")


prompt = """
    Sie sind ein hilfreicher Assistent für Autounfälle namens "crashy". Ihre Aufgabe
    ist es,
    einen umfassenden Schadensbericht basierend auf den bereitgestellten Fahrzeugbildern
    auf Deutsch zu
    erstellen. Nutzen Sie alle bereitgestellten Bilder und fordern Sie bei Bedarf
    zusätzliche
    Bilder oder Details an, um eine genaue Bewertung vornehmen zu können. Beschreiben
    Sie
    ausschließlich die sichtbaren Schäden auf den Bildern und vermeiden Sie es,
    zusätzliche
    Informationen einzubeziehen.

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
    - **Erforderlich**: Nein

    5. **Schadensort am Fahrzeug**:
    - Geben Sie an, wo sich der Schaden am Fahrzeug befindet (z.B. Front, Heck, Seiten,
    Dach).
    - **Erforderlich**: Nein

    6. **Brandgefahr**:
    - Bestätigen Sie, ob Anzeichen von Brand vorhanden sind (Ja/Nein).
    - **Erforderlich**: Nein

    7. **Kennzeichen**:
    - Erfassen Sie das Kennzeichen nur, wenn es klar lesbar und vollständig
    erkennbar ist und jedes Zeichen zu 100% sichtbar ist.
    - Wenn das Kennzeichen nicht zu 100% sichtbar ist, geben Sie `None` an.
    - **Erforderlich**: Nein

    8. **Zusätzliche Details**:
    - Fügen Sie eine detaillierte Beschreibung der sichtbaren Schäden hinzu,
        einschließlich
    der betroffenen Fahrzeugteile und der Art des Schadens
    (z.B. Dellen, Kratzer, gebrochene Spiegel).

    9. **Anzahl der gültigen Bilder**:
    - Geben Sie die Anzahl der Bilder an, die für die Bewertung des Schadens
    verwendet wurden. Ungültige Bilder sollten nicht berücksichtigt werden.
    - **Erforderlich**: Ja

    10. **Anzahl der eindeutigen Fahrzeuge**:
    - Geben Sie die Anzahl der eindeutigen Fahrzeuge an, die auf den Bildern
    zu sehen sind. Wenn mehrere Fahrzeuge auf den Bildern sichtbar sind, geben
    Sie die Anzahl der unterschiedlichen Fahrzeuge an.

    **Beispiel**:
    - Fahrzeug vorhanden: Ja
    - Erkannter Schaden: Ja
    - Vollständige Sichtbarkeit des Schadens: Ja
    - Schweregrad des Schadens: Mittel
    - Schadensort am Fahrzeug: Front
    - Brandgefahr: Nein
    - Kennzeichen: None
    - Zusätzliche Details: Es gibt eine große Delle auf der Motorhaube und
    einen Kratzer auf der Stoßstange.
    - Anzahl der gültigen Bilder: 3
    - Anzahl der eindeutigen Fahrzeuge: 1


    """


uploaded_file = st.file_uploader(
    "Bitte laden Sie ein " "Bild vom Schaden hoch", type=["jpg", "jpeg", "png"],
    accept_multiple_files=True)


if uploaded_file is not None:
    n_cols = (len(uploaded_file) + 3) // 4
    cols = st.columns(n_cols)
    for i in range(len(uploaded_file)):
        cols[i % n_cols].image(uploaded_file[i], caption=f"Foto Nr. {i+1}",
        use_column_width=True)

    # Function to encode the image
    def encode_image(data: list[bytes]) -> list[str]:
        """Encode the given image."""
        return [base64.b64encode(img).decode("utf-8") for img in data]



    base64_images = encode_image([file.getvalue() for file in uploaded_file])
    img_content = []
    for base64_image in base64_images:
        content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
        }
        img_content.append(content)


    # After receiving the response
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": img_content,
            },
        ],
        response_format=AccidentReport,
        temperature=0.1,
    )

    accident_report = response.choices[0].message.parsed
    st.write(accident_report )

    if not accident_report:
        st.write("Das Bild konnte leider nicht analysiert werden. Bitte laden Sie ein Bild vom gesamten Fahrzeug hoch.")
    else:
        for car in accident_report.cars:
            if not car.damage.fire_present and car.damage.damage_severity != "high":
                st.write(f"Fahrzeug {car.vehicle_id} Schadenbericht:")
                st.write(f"- Schweregrad des Schadens: {car.damage.damage_severity}")
                st.write(f"- Schadensort am Fahrzeug: {car.damage.damage_location}")
                st.write(f"- Kennzeichen: {car.damage.license_plate_number or 'None'}")
                st.write(f"- Zusätzliche Details: {car.damage.detailed_damage_description}")
            elif car.damage.fire_present:
                st.warning(f"Fahrzeug {car.vehicle_id}: Brandgefahr!")
            elif car.damage.damage_severity == "high":
                st.warning(f"Fahrzeug {car.vehicle_id}: Hoher Schaden!")

    # Additional form handling as needed

        @st.fragment
        def fill_out_form(accident_report: AccidentReport) -> None:
            for car in accident_report.cars:
                st.subheader(f"Fahrzeug {car.vehicle_id} Details")
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Name", placeholder="Ihr Name")
                    st.text_input("Telefonnummer", placeholder="Ihre Telefonnummer")
                    st.text_input("E-Mail-Adresse", placeholder="Ihre E-Mail-Adresse")
                    st.text_area("Anschrift", placeholder="Ihre Anschrift")
                with col2:
                    st.text_input("Schweregrad des Schadens", car.damage.damage_severity)
                    st.text_input("Schadensort am Fahrzeug", car.damage.damage_location)
                    st.text_input("Kennzeichen", car.damage.license_plate_number or "None")
                    st.text_area("Zusätzliche Details", car.damage.detailed_damage_description)
            st.write("Bitte überprüfen Sie die Angaben.")
            if st.button("Schaden melden"):
                # Handle form submission
                ...
                
        fill_out_form(accident_report)

