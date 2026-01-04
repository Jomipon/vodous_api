from openai import OpenAI
from supabase_client import supabase_anon, supabase_service

def supabase_create_bucket(bucket_name):
    """
    Create bucket in supabase
    
    :param bucket_name: Name of bucket
    """
    response = (
        supabase_service.storage
        .create_bucket(
            bucket_name,
            options={
                "public": False,
                "allowed_mime_types": ["audio/mpeg"],
                "file_size_limit": 50*1024,
            }
        )
    )
    if response.name == bucket_name:
        #ok
        return True
    else:
        # něco se nepovedlo
        return False

def supabase_get_bucket(bucket_name):
    """
    Return bucket if exists
    
    :param bucket_name: Name of bucket
    """
    bucket = supabase_service.storage.get_bucket(bucket_name)
    if not bucket:
        supabase_create_bucket(bucket_name)
        bucket = supabase_service.storage.get_bucket(bucket_name)
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

def get_word_detail(word_id):
    """
    Word detail from database
    
    :param word_id: Word ID
    """
    word_detail = supabase_anon.from_("word_content").select("word_id,word_content,tts_path").eq("word_id", word_id).execute()
    return word_detail.data

def upload_file_to_bucket(bucket_server, tts_path, word_tts):
    """
    Upload file to bucket in database
    
    :param bucket_server: Name bucket server
    :param tts_path: File path in bucket
    :param word_tts: File bytes
    """
    upload_responce = supabase_service.storage.from_(bucket_server).upload(
        path=tts_path,
        file=word_tts,
        file_options={
            "content-type": "audio/mpeg",
            "upsert": False,  # False = chyba, pokud už existuje
        },
    )
    return upload_responce
def word_file_name_bucket(tts_path, word_id):
    """
    Retrun file path in bucket
    
    :param tts_path: Path in bucket
    :param word_id: Word ID
    """
    if not tts_path:
        tts_path = f"mp3/{word_id}.mp3"
        supabase_anon.from_("word_content").update({"tts_path": tts_path}).eq("word_id", word_id).execute()
    return tts_path

def word_speech(word_id):
    """
    Return speech for word
    
    :param word_id: ID word
    """
    bucket_server = "words_tts"
    word_detail = get_word_detail(word_id)
    if len(word_detail) == 0:
        return ""
    tts_path = word_file_name_bucket(word_detail[0]["tts_path"], word_id)
    bucket = supabase_get_bucket(bucket_server)
    if not word_speech_file_exists(bucket.id, tts_path):
        word_tts = word_download_from_openai(word_detail[0]["word_content"])
        if not word_tts:
            return ""
        upload_responce = upload_file_to_bucket(bucket_server, tts_path, word_tts)
    tts_data = supabase_service.storage.from_(bucket.id).download(tts_path)
    return tts_data

def word_speech_file_exists(bucket_name, path: str) -> bool:
    """
    Test to exists file in bucket
    
    :param bucket_name: Bucket name
    :param path: File path
    :type path: str
    :return: Exists file in bucket
    :rtype: bool
    """
    folder, filename = path.rsplit("/", 1)
    res = supabase_service.storage.from_(bucket_name).list(folder)
    return any(obj["name"] == filename for obj in res)
