from openai import OpenAI

class openAIClient():
    client = None

    def create_client(self):
        self.client = OpenAI()

    def get_tts(self, input_text):
        with self.client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="marin",
            input=input_text,
            instructions="neutrally, slowly",
            response_format="mp3",
        ) as response:
            responce_stream = response.read()
        return responce_stream
