"""
Main program for start api
"""
from datetime import date, timedelta
from io import BytesIO
import uuid
import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from dotenv import load_dotenv
from supabase_client import supabase_anon as database_anon, supabase_service as database_service
from app.Endpoint.word import word_speech, word_detail_with_translate, word_rating, get_all_words_with_translate, create_word, random_word
from app.Endpoint.matching import matching_set_rating
from app.Endpoint.sentence import random_sentence, allTenses, check_change_sentence
from app.Endpoint.storytelling import get_random_topic, create_story, evaluate_retelling, story_speech
from app.Model.word import EnvelopeWordContentOut, WordContentIn, EnvelopeWordSpeechOut, EnvelopeWordRating, EnvelopeWordAllLanguages
from app.Model.matching import MatchingRating
from app.Model.sentence import SentenceType, SentenceCheckAnswer
from app.Model.storytelling import StorytellingStoryByTopic, StorytellingEvaluationStory

app = FastAPI(title="Vodouš API", version="0.1.0")

load_dotenv()

api_access_url = os.environ.get("API_ACCESS_URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=api_access_url,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_word_detail(word_id):
    """
    Return detail of word with translate
    
    :param word_id: Word ID
    """
    return word_detail_with_translate(word_id, database_anon)

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Test api run
    """
    return {"status": "OK"}

@app.get("/words/all/{language_from}/{language_to}", status_code=200, tags=["Word"], response_model=EnvelopeWordContentOut)
async def get_all_words(language_from, language_to):
    """
    Return all words with translate
    """
    data_responce = get_all_words_with_translate(database_anon, language_from, language_to)
    responce = {
        "status": "OK",
        "data": data_responce
        }
    return responce

@app.get("/word/detail/{word_id}", status_code=200, tags=["Word"], response_model=EnvelopeWordContentOut)
async def get_word(word_id: str):
    """
    Return detail of word with translate
    """
    word_detail = get_word_detail(word_id)
    return {
        "status": "OK", 
        "data": word_detail
    }

@app.post("/word", status_code=201, tags=["Word"], response_model=EnvelopeWordContentOut)
async def post_create_item(word: WordContentIn):
    """
    Create new word
    """
    word_data = create_word(word, database_anon)
    return {
        "status": "OK", 
        "data": [ word_data ]
    }

@app.get("/word/random/{id_seed}", status_code=200, tags=["Word"])# response_model=EnvelopeWordContentOut
async def get_random_word(id_seed: int, word_language_from = "EN", word_language_to = "CZ"):
    """
    Return random word
    
    :param id_seed: Seed for random core
    :type id_seed: seed
    """
    if id_seed <= 0:
        id_seed = abs(id_seed)
    if not word_language_from:
        word_language_from = "EN"
    if not word_language_to:
        word_language_to = "CZ"
    data = random_word(database_anon, id_seed, word_language_from, word_language_to)
    return {"status": "OK", "data": data}

@app.get("/word/speech/{word_id}", status_code=200, tags=["Word"]) #response_model=EnvelopeWordSpeechOut
def get_word_speech(word_id):
    """
    Return word with Text-To-Speech
    
    :param word_id: ID word
    """
    responce = word_speech(word_id, database_service, database_anon)
    if not responce:
        raise HTTPException(status_code=404, detail="Audio not found")
    return StreamingResponse(
        BytesIO(responce),
        media_type="audio/mpeg",  # pro mp3
        headers={"Content-Disposition": 'inline; filename="speech.mp3"'},
    )
@app.get("/storytelling/speech/{story_id}", status_code=200, tags=["StoryTelling"]) #response_model=EnvelopeWordSpeechOut
def get_story_speech(story_id):
    """
    Return story with Text-To-Speech
    
    :param story_id: ID storytelling result
    """
    responce = story_speech(story_id, database_service, database_anon)
    if not responce:
        raise HTTPException(status_code=404, detail="Audio not found")
    return StreamingResponse(
        BytesIO(responce),
        media_type="audio/mpeg",  # pro mp3
        headers={"Content-Disposition": 'inline; filename="speech.mp3"'},
    )

@app.post("/word/rating/{word_translate_id}/{rating}", status_code=200, tags=["Word"], response_model=EnvelopeWordRating)
def post_word_rating(word_translate_id: str, rating: float):
    """
    Rate word
    """
    word_rating(word_translate_id, rating, database_service)
    return {"status": "OK"}

@app.get("/word/languages", status_code=200, tags=["Word"])
def get_word_languages():
    """
    Return all supported languages
    """
    data = database_anon.from_("translate_all_languages").select("*").execute()
    return {
        "status:": "OK",
        "data": data.data
    }

@app.post("/matching/rating", status_code=201, tags=["Matching"])
def post_mathing_rating(rating: MatchingRating):
    """
    Rating for mathing - words vs button clicks counter
    """
    return matching_set_rating(rating, database_anon)

@app.get("/storytelling/topic", status_code=200, tags=["Storytelling"])
def get_storytelling_random_topic():
    """
    Return random topic for storytelling
    """
    topics_data = get_random_topic(database_anon)
    responce = {
        "status": "OK",
        "data": topics_data
        }
    return responce

@app.post("/storytelling/story", status_code=200, tags=["Storytelling"])
def get_storytelling_story(topic: StorytellingStoryByTopic):
    """
    return random topic
    """
    story = create_story(database_anon, database_service, topic)
    return {
        "status": "OK",
        "data": story
    }
@app.post("/storytelling/evaluation", status_code=200, tags=["Storytelling"])
def get_storytelling_evaluate_retelling(story: StorytellingEvaluationStory):
    """
    Return evaluation from sendet text
    
    :param story: Original story with student text to evaluation
    :type story: StorytellingEvaluationStory
    """
    feedback = evaluate_retelling(database_anon, story)
    return {
        "status": "OK",
        "data": feedback
    }

@app.get("/statistics/weekly", status_code=200, tags=["Statistics"])
def get_statistics_daily():
    """
    Return statistics of using vodous for week
    """
    data = database_anon.from_("matching_statistics_by_day").select("*").gte("date_serial", date.today()-timedelta(7)).execute()
    return {
        "status": "OK",
        "data": data
    }

@app.post("/sentence_check/sentence/random")
def post_random_sentence(sentence_type_filter: SentenceType):
    """
    Return random sentence from DB and AI with parameters
    """
    tense = sentence_type_filter.Tense
    sentence_type = sentence_type_filter.Type

    sentence_data = random_sentence(database_anon, tense, sentence_type)
    return {
        "status": "OK",
        "data": sentence_data
    }

#get tense all
@app.get("/sentence_check/sentence/all_tenses")
def get_all_tenses():
    """
    Return all tenses
    """
    tenses_data = allTenses(database_anon)
    return {
        "status": "OK",
        "data": tenses_data
    }

# check sentence tense
@app.post("/sentence_check/sentence/check")
def post_sentense_check(check_answer: SentenceCheckAnswer):
    """
    Check new sentence
    """
    check_data = check_change_sentence(database_anon, check_answer.SourceSentence, check_answer.NewSentence, check_answer.TargetTense, check_answer.TargetTenseType)
    return {
        "status": "OK",
        "data": check_data
    }
"""
{
    "status": "OK",
    "data": {
        "tense": "past",
        "target_sentence_type": "affirmative",
        "is_correct": false,
        "corrected_sentence": "Sarah had picked up the package from the post office yesterday.",
        "corrected_czech_translation": "Sarah si včera vyzvedla balíček na poště.",
        "kept_meaning": true,
        "kept_phrasal_verb": true,
        "errors": [
            {
                "category": "tense",
                "problem": "Incorrect tense: past simple instead of past perfect.",
                "fix": "Use past perfect tense: 'had picked up'."
            }
        ],
        "short_feedback_cz": "Použili jste špatný čas. Měl by být použit předminulý čas.",
        "tips_cz": [
            "Použijte předminulý čas pro činnosti, které se staly před jiným momentem v minulosti.",
            "Ujistěte se, že správně používáte frázové sloveso v daném čase.",
            "Pamatujte, že předminulý čas vyžaduje pomocné sloveso 'had'.",
            "Dodržujte původní význam věty."
        ]
    }
}
"""
# change sentence type
# change sentence tense
