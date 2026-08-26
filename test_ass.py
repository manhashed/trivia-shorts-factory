import asyncio
import edge_tts

async def main():
    text = "Twinkle, twinkle, little star, how I wonder what you are."
    communicate = edge_tts.Communicate(text, "en-US-AnaNeural")
    
    boundaries = []
    with open("test_audio.mp3", "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                boundaries.append(chunk)
                
    for b in boundaries:
        print(b)

asyncio.run(main())
