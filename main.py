"""
Main program for start api
"""
from io import BytesIO
import random
import uuid
import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from dotenv import load_dotenv
from supabase_client import supabase_anon as database_anon, supabase_service as database_service
from app.Endpoint.word import word_speech, word_detail_with_translate, word_rating
from app.Endpoint.matching import matching_set_rating
from app.Model.word import EnvelopeWordContentOut, WordContentIn, EnvelopeWordSpeechOut, EnvelopeWordRating, EnvelopeWordAllLanguages
from app.Model.matching import MatchingRating
from app.Model.storytelling import StorytellingStoryByTopic, StorytellingEvaluationStory

from app.Endpoint.openAI_client import openAIClient


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
    querry = database_anon.from_("words_all_with_translate").select("*")
    querry = querry.eq("word_language_from", language_from)
    querry = querry.eq("valid_from", True)
    querry = querry.eq("word_language_to", language_to)
    querry = querry.order("word_id_from")
    querry = querry.order("word_translate_id")
    querry = querry.order("word_id_to")
    try:
        word_content_data = querry.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error in comunation with database") from e
    tran = {}
    for word in word_content_data.data:
        if word["word_id_from"] not in tran:
            tran[word["word_id_from"]] = []
        tran[word["word_id_from"]].append(
            {
                "word_id": word["word_id_to"],
                "word_content": word["word_content_to"],
                "word_language": word["word_language_to"],
                "valid": word["valid_to"],
                "note": word["note_to"]
            }
        )
    data_responce = []
    for word in word_content_data.data:
        data_responce.append(
            {
                "word_id": word["word_id_from"],
                "word_content": word["word_content_from"],
                "word_language": word["word_language_from"],
                "valid": word["valid_from"],
                "note": word["note_from"],
                "translate": tran[word["word_id_from"]]
            }
            )
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
    if not word_id:
        raise HTTPException(status_code=500, detail="Word ID not exists")
    word_detail = get_word_detail(word_id)
    return {
        "status": "OK", 
        "data": word_detail
    }

@app.post("/word", status_code=201, tags=["Word"], response_model=EnvelopeWordContentOut)
async def create_item(word: WordContentIn):
    """
    Create new word
    """
    if not word.word_id:
        word.word_id = str(uuid.uuid4())
    try:
        data = database_anon.from_("word_content").select("*").eq("word_id", word.word_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=e) from e
    if len(data.data) > 0:
        raise HTTPException(status_code=500, detail="Word ID is exists")
    insert = {
        "word_id": word.word_id,
        "word_content": word.word_content,
        "word_language": word.word_language,
        "valid": word.valid,
        "note": word.note
    }
    try:
        database_anon.from_("word_content").insert(insert).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=e) from e
    try:
        resp = database_anon.from_("word_content").select("*").eq("word_id", word.word_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=e) from e
    if len(resp.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Word with id '{word.word_id}' not found"
    )
    return {
        "status": "OK", 
        "data": 
        [
            {
                "word_id": resp.data[0]["word_id"],
                "word_content": resp.data[0]["word_content"],
                "word_language": resp.data[0]["word_language"],
                "valid": resp.data[0]["valid"],
                "note": resp.data[0]["note"],
                "translate": []
            }
        ]
    }

@app.get("/word/random/{id_seed}", status_code=200, tags=["Word"])# response_model=EnvelopeWordContentOut
async def get_random_word(id_seed: int, word_language_from = "EN", word_language_to = "CZ"):
    """
    Return random word
    
    :param id_seed: Seed for random core
    :type id_seed: seed
    """
    if id_seed <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seed ID must be higher then 0")
    if not word_language_from:
        word_language_from = "EN"
    if not word_language_to:
        word_language_to = "CZ"
    resp = database_anon.from_("words_all_with_translate").select("*").eq("word_language_from", word_language_from).eq("word_language_to", word_language_to).order("random_id", desc=True).execute()
    if len(resp.data) > 0:
        random.seed(id_seed)
        random.seed()
        index = random.randint(0,len(resp.data)-1)
        data = resp.data[index]
    else:
        data = []
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
    topics = database_anon.from_("storytelling_all_topics").select("*")
    try:
        topics_data = topics.execute()
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail="Error in comunation with database") from e
    if len(topics_data.data) > 0:
        topics_data = topics_data.data[0]
    else:
        topics_data = None
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
    client = openAIClient()
    client.create_client()
    story = client.get_story_by_topic(topic, level = "B1-B2", min_words = 140, max_words = 180)
    topic_dupl = database_anon.from_("storytelling_topics").select("*").eq("topic_text", story.title).execute()
    if len(topic_dupl.data) == 0:
        database_anon.from_("storytelling_topics").insert({"topic_text": story.title}).execute()
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
    client = openAIClient()
    client.create_client()
    feedback = client.evaluate_retelling(original_text=story.original, student_text=story.student)
    result_data =  { 
        "story_text": story.original,
        "corrected_text": feedback.corrected_text,
        "score_0_100": feedback.score_0_100,
        "cefr_estimate": feedback.cefr_estimate,
        "short_feedback": feedback.short_feedback,
        "strengths": feedback.strengths,
        "improvements": feedback.improvements,
        "top_corrections": feedback.top_corrections
        }
    database_anon.from_("storytelling_result").insert(result_data).execute()
    return feedback
