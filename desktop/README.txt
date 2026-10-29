FemaleVocal — live male-to-female voice changer

This copy uses the IndicVoiceChanger Seed-VC model with one public female
reference voice. The target reference is the female `s1p1` sample from the
public Seed-VC demo set. It is intended for English, Hindi, and Marathi speech.
The app processes audio on your PC; it does not send microphone audio to a
server.

Open FemaleVocalIndic.exe from the complete FemaleVocalIndic folder.
Choose your microphone and output device, select NVIDIA GPU for lower delay,
and start conversion. For WhatsApp, use CABLE Input as the app output and
CABLE Output as WhatsApp's microphone. A virtual audio cable is installed
separately.

The first start downloads shared model components once. This can require
about 1–2 GB of internet data and is saved under
%LOCALAPPDATA%\FemaleVocal\models. After that, the model runs locally.
Use a microphone and headphones. RNNoise can reduce steady room noise, but
speech quality also depends on the input device and speaking distance.

The app uses short audio blocks and reports its estimated delay and processing
time while live. Voice quality varies by language, mic, and speaker; try a
short call before relying on it.

See MODEL-LICENSE.txt, REFERENCE-VOICE-SOURCE.txt, SEEDVC-LICENSE.txt, and
THIRD-PARTY-NOTICES.txt.
This local build includes the matching source archive.
