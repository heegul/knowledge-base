import os
import soundfile as sf
from TTS.api import TTS

def text_to_speech(text, output_file):
    # Initialize TTS model
    tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=True, gpu=False)
    
    # Synthesize speech
    waveform = tts.tts(text)
    
    # Save the output
    sf.write(output_file, waveform, samplerate=22050)
    print(f'Audio content written to "{output_file}"')

# Example usage
text = "Hello, this is a sample text to convert to speech."
output_file = "output.wav"
text_to_speech(text, output_file)
