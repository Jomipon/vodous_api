"""
Endpoint for path /word/*
"""
#from fastapi import HTTPException, status
#from openai import OpenAI
import random
import uuid
from app.Endpoint.openAI_client import openAIClient
from app.Endpoint.bucket import supabase_get_bucket, supabase_file_exists, upload_file_to_bucket
from openai import OpenAI
from app.Model.word import WordContentIn



def word_download_from_openai(input_text):
    """
    Download speech from openAI from text
    
    :param input_text: Text to speech
    """
    try:
        client = openAIClient()
        client.create_client()
        responce_stream = client.get_tts(input_text)
    except Exception as e:
        responce_stream = None
    return responce_stream

def word_detail(word_id, storage_client_anon):
    """
    Word detail from database
    
    :param word_id: Word ID
    """
    word_detail = storage_client_anon.from_("word_content").select("word_id,word_content,tts_path").eq("word_id", word_id).execute()
    return word_detail.data
def word_detail_with_translate(word_id, storage_client_anon):
    """
    Return word detail with translate
    
    :param word_id: Word ID
    """
    if not word_id:
        raise Exception("Word ID not exists")
    try:
        resp = storage_client_anon.from_("words_all_with_translate").select("*").eq("word_id_from", word_id).execute()
    except Exception as e:
        raise Exception("Error in comunation with database") from e
        #raise HTTPException(status_code=500, detail="Error in comunation with database") from e
    if len(resp.data) == 0:
        raise Exception(f"Word with id '{word_id}' not found") from e
        #raise HTTPException(
        #    status_code=status.HTTP_404_NOT_FOUND,
        #    detail=f"Word with id '{word_id}' not found"
        #)
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

def word_file_in_name_bucket(tts_path, word_id, storage_client_anon):
    """
    Retrun file path in bucket
    
    :param tts_path: Path in bucket
    :param word_id: Word ID
    """
    if not tts_path:
        tts_path = f"mp3/{word_id}.mp3"
        storage_client_anon.from_("word_content").update({"tts_path": tts_path}).eq("word_id", word_id).execute()
    return tts_path


def word_speech(word_id, storage_client_service, storage_client_anon):
    """
    Return speech for word
    
    :param word_id: ID word
    """
    bucket_server = "words_tts"
    detail = word_detail(word_id, storage_client_anon)
    if len(detail) == 0:
        return ""
    tts_path = word_file_in_name_bucket(detail[0]["tts_path"], word_id, storage_client_anon)
    bucket = supabase_get_bucket(bucket_server, storage_client_service)
    if not supabase_file_exists(bucket.id, tts_path, storage_client_service):
        word_tts = word_download_from_openai(detail[0]["word_content"])
        if not word_tts:
            return ""
        upload_responce = upload_file_to_bucket(bucket_server, tts_path, word_tts, storage_client_service)
    tts_data = storage_client_service.storage.from_(bucket.id).download(tts_path)
    return tts_data


def word_rating_append(word_translate_id, rating, storage_client_anon):
    """
    Add rating for word to database
    
    :param word_translate_id: Translate ID
    :param rating: Rating
    :param storage_client_anon: Database client
    """
    insert_data = {}
    insert_data["word_translate_id"] = word_translate_id
    insert_data["success_rate"] = rating
    storage_client_anon.from_("word_translate_success_rate").insert(insert_data).execute()

def translate_rating_recalculation(word_translate_id, storage_client_anon):
    """
    Call function in database for recalculation rating for word
    
    :param word_translate_id: Translate ID
    :param storage_client_anon: Database client
    """
    storage_client_anon.rpc("translate_rating_recalculation", params={"p_word_translate_id": word_translate_id}).execute()


def word_rating(word_translate_id, rating, storage_client_anon):
    """
    Add rating and recalculating for word
    
    :param word_translate_id: Translate ID
    :param rating: Rating (0-low, 1-high)
    :param storage_client_anon: Database client
    """
    word_rating_append(word_translate_id, rating, storage_client_anon)
    translate_rating_recalculation(word_translate_id, storage_client_anon)

def get_all_words_with_translate(database_anon, language_from, language_to):
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
        raise Exception("Error in comunation with database") from e
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
    return data_responce

def create_word(word: WordContentIn, database_anon):
    """
    Create new word
    """
    if not word.word_id:
        word.word_id = str(uuid.uuid4())
    try:
        data = database_anon.from_("word_content").select("*").eq("word_id", word.word_id).execute()
    except Exception as e:
        raise Exception("Error in communication with database")
    if len(data.data) > 0:
        raise Exception("Word ID is exists")
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
        raise Exception("Error in comunation with database") from e
    try:
        resp = database_anon.from_("word_content").select("*").eq("word_id", word.word_id).execute()
    except Exception as e:
        raise Exception("Error in comunation with database") from e
    if len(resp.data) == 0:
        raise Exception(f"Word with id '{word.word_id}' not found") from e
    return {
                "word_id": resp.data[0]["word_id"],
                "word_content": resp.data[0]["word_content"],
                "word_language": resp.data[0]["word_language"],
                "valid": resp.data[0]["valid"],
                "note": resp.data[0]["note"],
                "translate": []
            }

def random_word(database_anon, id_seed, word_language_from, word_language_to):
    resp = database_anon.from_("words_all_with_translate").select("*").eq("word_language_from", word_language_from).eq("word_language_to", word_language_to).order("random_id", desc=True).execute()
    if len(resp.data) > 0:
        random.seed(id_seed)
        random.seed()
        index = random.randint(0,len(resp.data)-1)
        data = resp.data[index]
    else:
        data = []
    return data
