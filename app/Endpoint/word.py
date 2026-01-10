"""
Endpoint for path /word/*
"""
from fastapi import HTTPException, status
from openai import OpenAI

def supabase_create_bucket(bucket_name, storage_client_service):
    """
    Create bucket in supabase
    
    :param bucket_name: Name of bucket
    """
    response = (
        storage_client_service.storage
        .create_bucket(
            bucket_name,
            options={
                "public": False,
                "allowed_mime_types": ["audio/mpeg"],
                "file_size_limit": 50*1024,
            }
        )
    )
    return response.name == bucket_name

def supabase_get_bucket(bucket_name, storage_client_service):
    """
    Return bucket if exists
    
    :param bucket_name: Name of bucket
    """
    bucket = storage_client_service.storage.get_bucket(bucket_name)
    if not bucket:
        supabase_create_bucket(bucket_name, storage_client_service)
        bucket = storage_client_service.storage.get_bucket(bucket_name)
    return bucket

def word_download_from_openai(input_text):
    """
    Download speech from openAI from text
    
    :param input_text: Text to speech
    """
    try:
        client = OpenAI()
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="marin",
            input=input_text,
            instructions="neutrally, slowly",
            response_format="mp3",
        ) as response:
            responce_stream = response.read()
    except:
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
    try:
        resp = storage_client_anon.from_("words_all_with_translate").select("*").eq("word_id_from", word_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error in comunation with database") from e
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

def upload_file_to_bucket(bucket_server, tts_path, word_tts, storage_client_service):
    """
    Upload file to bucket in database
    
    :param bucket_server: Name bucket server
    :param tts_path: File path in bucket
    :param word_tts: File bytes
    """
    upload_responce = storage_client_service.storage.from_(bucket_server).upload(
        path=tts_path,
        file=word_tts,
        file_options={
            "content-type": "audio/mpeg",
            "upsert": False,  # False = chyba, pokud už existuje
        },
    )
    return upload_responce
def word_file_name_bucket(tts_path, word_id, storage_client_anon):
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
    tts_path = word_file_name_bucket(detail[0]["tts_path"], word_id, storage_client_anon)
    bucket = supabase_get_bucket(bucket_server, storage_client_service)
    if not word_speech_file_exists(bucket.id, tts_path, storage_client_service):
        word_tts = word_download_from_openai(detail[0]["word_content"])
        if not word_tts:
            return ""
        upload_responce = upload_file_to_bucket(bucket_server, tts_path, word_tts, storage_client_service)
    tts_data = storage_client_service.storage.from_(bucket.id).download(tts_path)
    return tts_data

def word_speech_file_exists(bucket_name, path: str, storage_client_service) -> bool:
    """
    Test to exists file in bucket
    
    :param bucket_name: Bucket name
    :param path: File path
    :type path: str
    :return: Exists file in bucket
    :rtype: bool
    """
    folder, filename = path.rsplit("/", 1)
    res = storage_client_service.storage.from_(bucket_name).list(folder)
    return any(obj["name"] == filename for obj in res)

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


