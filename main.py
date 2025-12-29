"""
Main program for start api
"""
import random
import uuid
import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase_client import supabase
from Model.word import EnvelopeWordContentOut, WordContentIn

app = FastAPI(title="Vodouš API", version="0.1.0")
database = supabase

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
    
    :param word_id: Description
    """
    try:
        resp = database.from_("words_all_with_translate").select("*").eq("word_id_from", word_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=e) from e
    if len(resp.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Word with id '{word_id}' not found"
    )
    translate_all = []
    for translate in resp.data:
        if translate["word_id_to"]:
            translate_all.append({"word_id": translate["word_id_to"],
                    "word_content": translate["word_content_to"],
                    "word_language": translate["word_language_to"],
                    "valid": translate["valid_to"],
                    "note": translate["note_to"]})
    return [
            {
                "word_id": resp.data[0]["word_id_from"],
                "word_content": resp.data[0]["word_content_from"],
                "word_language": resp.data[0]["word_language_from"],
                "valid": resp.data[0]["valid_from"],
                "note": resp.data[0]["note_from"],
                "translate": translate_all
            }
        ]


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Test api run
    """
    return {"status": "ok"}

@app.get("/words/{language_from}/{language_to}", status_code=200, tags=["Word"], response_model=EnvelopeWordContentOut)
async def get_all_words(language_from, language_to):
    """
    Return all words with translate
    """
    querry = database.from_("words_all_with_translate").select("*")
    querry = querry.eq("word_language_from", language_from)
    querry = querry.eq("valid_from", True)
    querry = querry.eq("word_language_to", language_to)
    querry = querry.order("word_id_from")
    querry = querry.order("word_translate_id")
    querry = querry.order("word_id_to")
    word_content_data = querry.execute()
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

@app.get("/word/{word_id}", status_code=200, tags=["Word"], response_model=EnvelopeWordContentOut)
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
        data = database.from_("word_content").select("*").eq("word_id", word.word_id).execute()
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
        database.from_("word_content").insert(insert).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=e) from e
    try:
        resp = database.from_("word_content").select("*").eq("word_id", word.word_id).execute()
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
async def get_random_word(id_seed: int):
    """
    Return random word
    
    :param id_seed: Seed for random core
    :type id_seed: seed
    """
    if id_seed <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seed ID must be higher then 0")
    resp = database.from_("words_all_with_translate").select("*").eq("word_language_from", "EN").order("random_id", desc=True).execute()
    random.seed(id_seed)
    random.seed()
    index = random.randint(0,len(resp.data)-1)
    return {"status": "ok", "data": resp.data[index]}

