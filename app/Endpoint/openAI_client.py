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

Tense = Literal["past", "present", "future"]
SentenceType = Literal["affirmative", "negative", "question"]
class SentenceTaskResult(BaseModel):
    tense: Tense
    sentence_type: SentenceType
    sentence: str = Field(description="Exactly ONE English sentence, max 20 words.")
    czech_translation: str = Field(description="Czech translation of the sentence (one sentence).")
    phrasal_verb: str = Field(description="The phrasal verb used in the sentence, e.g. 'give up'.")
    word_count: int = Field(ge=1, le=20)
class ErrorItem(BaseModel):
    category: Literal["tense", "sentence_type", "grammar", "word_order", "meaning", "phrasal_verb", "spelling", "punctuation"]
    problem: str = Field(description="What is wrong (short).")
    fix: str = Field(description="How to fix it (short).")
class TransformationFeedback(BaseModel):
    tense: Tense
    target_sentence_type: SentenceType
    is_correct: bool
    corrected_sentence: str
    corrected_czech_translation: str
    kept_meaning: bool
    kept_phrasal_verb: bool
    errors: List[ErrorItem]
    short_feedback_cz: str = Field(description="1–3 sentences in Czech.")
    tips_cz: List[str] = Field(description="2–4 short actionable tips in Czech.")

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
    def get_story_by_topic(self, topic: str, level: str = "B1-B2", min_words: int = 140, max_words: int = 180, tense = "PAST"):
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
            f"Target tense: {tense}.\n"
            "Rules:\n"
            "- Write the main narration primarily in the target tense (aim for 80–90%).\n"
            "- Avoid unnecessary tense switching.\n"
            "- If a different tense is needed, keep it brief and clearly motivated.\n"
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
    def get_sentence_with_parameters(self, tense: str, sentence_type: str) -> Feedback:
        system_instructions = (
        "You are an English teacher creating short practice sentences.\n"
        "Hard rules (must follow):\n"
        "- Output must follow the provided JSON schema.\n"
        "- Produce EXACTLY ONE sentence in English.\n"
        "- Max 20 words.\n"
        "- The sentence MUST contain a phrasal verb (verb + particle/preposition), e.g., 'pick up', 'turn down'.\n"
        "- The person/subject must be random (invent a realistic person or role).\n"
        "- Use the requested tense for the main verb phrase.\n"
        "- Use the requested sentence type: affirmative / negative / question.\n"
        "- Do not add a second English sentence. No extra commentary.\n"
        "- ALSO return a Czech translation of the English sentence (one sentence).\n"
        "Tense guidance:\n"
        "- past: simple past or past continuous when natural.\n"
        "- present: simple present or present continuous when natural.\n"
        "- future: will / be going to / present continuous for arranged plans.\n"
        "Translation guidance:\n"
        "- The Czech translation must match the meaning and sentence type.\n"
        "- Keep it natural Czech.\n"
        )
        user_prompt = (
        f"Parameters:\n"
        f"- tense: {tense}\n"
        f"- sentence_type: {sentence_type}\n"
        "Return JSON only."
        )
        MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")
        response = self.client.responses.parse(
            model=MODEL,
            instructions=system_instructions,
            input=user_prompt,
            text_format=SentenceTaskResult,
            store=False,
        )
        return response.output_parsed
    def get_check_sentence(self, original_sentence, student_sentence, target_tense, target_sentence_type):
        system_instructions = (
        "You are an English teacher checking a student's sentence transformation.\n"
        "The student must transform the original sentence into the TARGET sentence type\n"
        "while keeping the meaning as close as possible and keeping the same tense.\n\n"
        "Rules to evaluate:\n"
        "- Check the TARGET sentence type: affirmative / negative / question.\n"
        "- Check that the tense remains the requested tense (past/present/future).\n"
        "- Check grammar (auxiliaries, negation, question formation, word order).\n"
        "- Check meaning is preserved.\n"
        "- Check the phrasal verb is preserved (same phrasal verb, if possible).\n\n"
        "Output MUST follow the provided JSON schema only. No extra text."
        )
        user_input = (
            f"TENSE: {target_tense}\n"
            f"TARGET_SENTENCE_TYPE: {target_sentence_type}\n"
            f"ORIGINAL_SENTENCE:\n{original_sentence}\n\n"
            f"STUDENT_SENTENCE:\n{student_sentence}\n\n"
            "Return JSON only."
            )
        #f"ORIGINAL_PHRASAL_VERB: {original_phrasal_verb}\n\n"
        MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")
        resp = self.client.responses.parse(
            model=MODEL,
            instructions=system_instructions,
            input=user_input,
            text_format=TransformationFeedback,
            store=False,
        )
        return resp.output_parsed
        