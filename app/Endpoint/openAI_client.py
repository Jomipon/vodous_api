from openai import OpenAI
import os
from typing import List, Literal
from pydantic import BaseModel, Field

class Feedback(BaseModel):
    corrected_text: str = Field(description="Corrected version of the student's retelling.")
    score_0_100: int = Field(ge=0, le=100)
    cefr_estimate: Literal["A2", "B1", "B2", "C1"]
    short_feedback: str = Field(description="1–3 short sentences, in Czech, focusing on the most important advice.")
    strengths: List[str] = Field(description="2–4 bullet points")
    improvements: List[str] = Field(description="2–4 bullet points")
    top_corrections: List[str] = Field(description="3–6 items: what was wrong -> better version (brief)")

class openAIClient():
    client = None

    def create_client(self):
        self.client = OpenAI()

    def get_tts(self, input_text):
        """
        Get speech from text
        """
        with self.client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="marin",
            input=input_text,
            instructions="neutrally, slowly",
            response_format="mp3",
        ) as response:
            responce_stream = response.read()
        return responce_stream
    def get_story_by_topic(self, topic: str, level: str = "B1-B2", min_words: int = 140, max_words: int = 180):
        class ReadingText(BaseModel):
            level: Literal["B1", "B2", "B1-B2"]
            title: str
            text: str
            word_count: int = Field(ge=80, le=260)
            vocab: List[str] = Field(description="6–10 užitečných slovíček/kolokací z textu")
            questions: List[str] = Field(description="2–4 krátké otázky na porozumění")

        system_instructions = (
            "You are an English teacher. Create a short reading text for learners.\n"
            "Requirements:\n"
            f"- CEFR level: {level}\n"
            f"- Length: {min_words}-{max_words} words (natural English, clear sentences)\n"
            "- Avoid advanced idioms and very rare vocabulary.\n"
            "- Keep it interesting and realistic.\n"
            "- Provide 6–10 useful vocabulary items from the text.\n"
            "- Provide 2–4 short comprehension questions.\n"
        )
        user_prompt = (
            f"Topic: {topic}\n"
            "Write ONE text (not multiple options)."
        )
        MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")  # můžeš změnit třeba na "gpt-5.2"
        # store=False = omezíš ukládání na straně API (hodí se pro výukové aplikace)
        response = self.client.responses.parse(
            model=MODEL,
            instructions=system_instructions,
            input=user_prompt,
            text_format=ReadingText,
            store=False,
        )
        return response.output_parsed
    def evaluate_retelling(self, original_text: str, student_text: str) -> Feedback:
        system_instructions = (
            "You are an English tutor.\n"
            "Task:\n"
            "1) Read the original text and the student's retelling.\n"
            "2) Produce a corrected version of the student's retelling in English.\n"
            "   - Keep the student's meaning and style as much as possible.\n"
            "   - Fix grammar, word choice, and unnatural phrasing.\n"
            "3) Give a short evaluation in Czech (1–3 sentences).\n"
            "4) Provide score 0–100, an approximate CEFR estimate, strengths, improvements,\n"
            "   and a short list of top corrections (brief 'wrong -> better').\n"
            "Be kind, specific, and concise."
        )

        user_prompt = (
            "ORIGINAL TEXT:\n"
            f"{original_text}\n\n"
            "STUDENT RETELLING:\n"
            f"{student_text}\n"
        )
        MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")
        response = self.client.responses.parse(
            model=MODEL,
            instructions=system_instructions,
            input=user_prompt,
            text_format=Feedback,
            store=False,
        )
        return response.output_parsed
