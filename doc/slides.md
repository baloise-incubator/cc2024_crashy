## crashy
Codecamp 2024 - Sercan, Patrick

![crashy](crashy.jpg)

---

## Project Objectives?
- simplify car damage reporting
  - only speak and
  - take pictures
- speech to text to extract incident context
- extract damage information from the given images
- extract image metadata to get location and time
- user can revise the generated damage report and finalize it
---

![crashy process flow](process_flow.jpg)

---

## Demo
- case 1: accident with an animal
- case 2: car radio theft
- case 3: minor car damage

---

## Conclusions:
- given JSON structure can reliably be extracted
- gpt4o object detection yields acceptable results
- english yields better damage descriptions
- gpt4o visual model is affordable (<0.2 cents/pic)
- speech to text works if audio quality is good
- swiss german words are not recognized
- overall service latency is really good
- gpt4o audio preview is atm. no better than currently used whisper
- https://github.com/baloise-incubator/cc2024_crashy
