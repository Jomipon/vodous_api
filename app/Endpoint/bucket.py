

def supabase_create_bucket(bucket_name, storage_client_service):
    """
    Create bucket in supabase
    
    :param bucket_name: Name of bucket
    :param storage_client_service: client to server
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
    return response

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
def supabase_file_exists(bucket_name, path: str, storage_client_service) -> bool:
    """
    Test to exists file in bucket
    
    :param bucket_name: Bucket name
    :param path: File path
    :type path: str
    :return: Exists file in bucket
    :rtype: bool
    """
    return storage_client_service.storage.from_(bucket_name).exists(path)
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
