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
from app.Model.word import EnvelopeWordContentOut, WordContentIn, EnvelopeWordSpeechOut
from app.Model.matching import MatchingRating


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
    return {"status": "ok"}


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
        "status": "ok",
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

@app.get("/word/random/{id_seed}", status_code=200, tags=["Word"])
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
    return {"status": "ok", "data": data}

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

@app.post("/word/rating/{word_translate_id}/{rating}", status_code=200, tags=["Word"])
def post_word_rating(word_translate_id: str, rating: float):
    """
    Rate word
    """
    word_rating(word_translate_id, rating, database_service)
    return {"status": "ok"}

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
