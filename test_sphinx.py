import sys
try:
    from pocketsphinx import Decoder
    # Test if keyphrase is supported
    decoder = Decoder(samprate=16000, keyphrase="jarvis", kws_threshold=1e-20)
    print("Keyword spotting mode works!")
except Exception as e:
    print(f"Error: {e}")
