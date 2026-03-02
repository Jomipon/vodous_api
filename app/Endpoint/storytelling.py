from uuid import uuid4
from app.Model.storytelling import StorytellingEvaluationStory
from app.Endpoint.openAI_client import openAIClient
from app.Endpoint.bucket import supabase_get_bucket, supabase_file_exists, upload_file_to_bucket


def get_random_topic(database_anon):
    """
    Get random topic from DB
    """
    topics = database_anon.from_("storytelling_all_topics").select("*")
    try:
        topics_data = topics.execute()
    except Exception as e:
        raise Exception("Error in comunation with database")
    if len(topics_data.data) > 0:
        topics_data = topics_data.data[0]
    else:
        topics_data = None
    return topics_data

def story_to_database(database_anon, story_title, story_text, story_title_tts_path, story_text_tts_path):
    data_ins = {"story_title": story_title, "story_text":  story_text, "story_title_tts_path": story_title_tts_path, "story_text_tts_path": story_text_tts_path}
    story_db = database_anon.from_("storytelling_story").insert(data_ins).execute()
    return story_db

def text_to_speech(ai_client, text_to_speech):
    return ai_client.get_tts(text_to_speech)

def get_story_from_AI(client_ai, topic):
    """
    Call OpenAI and return story by topic
    """
    client_ai.create_client()
    story = client_ai.get_story_by_topic(topic.topic, level = "B1-B2", min_words = 140, max_words = 180, tense = topic.tense)
    return story

def create_story(storage_client_anon, storage_client_service, topic):
    """
    Create new story by topic
    """
    client = openAIClient()
    # openAI Get story from topic
    story = get_story_from_AI(client, topic)
    
    # tts from story title
    tts_story_title = text_to_speech(client, story.title)
    # prepare bucket
    bucket_path = "mp3/"
    #story_title_tts_path = f"{str(uuid4())}.mp3"
    story_title_tts_path = f"{str(uuid4())}"
    bucket_server = "words_tts"
    supabase_get_bucket(bucket_server, storage_client_service)

    # upload story title to bucket
    upload_responce = upload_file_to_bucket(bucket_server, bucket_path+story_title_tts_path+".mp3", tts_story_title, storage_client_service)
    
    # tts from story text
    tts_story_text = text_to_speech(client, story.text)
    # upload story text to bucket
    #story_text_tts_path = f"{str(uuid4())}.mp3"
    story_text_tts_path = f"{str(uuid4())}"
    upload_responce = upload_file_to_bucket(bucket_server, bucket_path + story_text_tts_path+".mp3", tts_story_text, storage_client_service)

    # insert topic to DB
    topic_dupl = storage_client_anon.from_("storytelling_topics").select("storytelling_topics_id").eq("topic_text", story.title).execute()
    if len(topic_dupl.data) == 0:
        storage_client_anon.from_("storytelling_topics").insert({"topic_text": story.title, "storytelling_topics_id": str(uuid4())}).execute()
        topic_dupl = storage_client_anon.from_("storytelling_topics").select("storytelling_topics_id").eq("topic_text", story.title).execute()
    topics_id = topic_dupl.data[0]["storytelling_topics_id"]
    # insert story to DB
    story_db = story_to_database(storage_client_anon, story.title, story.text, story_title_tts_path, story_text_tts_path)
    #"story_title_tts_path": story_title_tts_path, "story_text_tts_path": story_text_tts_path
    print(f"{story_db.data[0]["storytelling_story_id"]=}")
    return {"level": story.level, "title": story.title, "text": story.text, "word_count": story.word_count, "storytelling_topics_id": topics_id, "storytelling_story_id": story_db.data[0]["storytelling_story_id"]}# : story_db.storytelling_story_id



def evaluate_retelling(database_anon, story: StorytellingEvaluationStory):
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

def story_result_detail(story_id, storage_client_anon):
    """
    Story result detail from database
    
    :param story_id: Story ID
    """
    story_result_detail = storage_client_anon.from_("storytelling_result").select("storytelling_result_id,story_text,story_text_tts_path").eq("storytelling_result_id", story_id).execute()
    return story_result_detail.data

def story_topic_detail(story_id, storage_client_anon):
    """
    Story topic detail from database
    
    :param story_id: Story ID
    """
    story_topic_detail = storage_client_anon.from_("storytelling_topics").select("storytelling_topics_id,topic_text,topic_tts_path").eq("storytelling_topics_id", story_id).execute()
    return story_topic_detail.data

def story_text_detail(story_id, storage_client_anon):
    """
    Story story detail from database
    
    :param story_id: Story ID
    """
    story_topic_detail = storage_client_anon.from_("storytelling_story").select("storytelling_story_id,story_title,story_text,story_title_tts_path,story_text_tts_path").eq("storytelling_story_id", story_id).execute()
    return story_topic_detail.data

def story_file_in_name_bucket(tts_path, story_id, storage_client_anon):
    """
    Retrun file path in bucket
    
    :param tts_path: Path in bucket
    :param word_id: Word ID
    """
    if not tts_path:
        tts_path = f"mp3/{story_id}.mp3"
        storage_client_anon.from_("storytelling_result").update({"story_text_tts_path": tts_path}).eq("storytelling_result_id", story_id).execute()
    return tts_path
def story_download_from_openai(input_text):
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

def story_speech(story_id, storage_client_service, storage_client_anon):
    """
    Return speech for story
    
    :param story_id: ID story
    """
    bucket_server = "words_tts"
    detail = story_text_detail(story_id, storage_client_anon)
    if len(detail) == 0:
        return ""
    tts_path = story_file_in_name_bucket(detail[0]["story_text_tts_path"], story_id, storage_client_anon)
    bucket = supabase_get_bucket(bucket_server, storage_client_service)
    if not supabase_file_exists(bucket.id, tts_path, storage_client_service):
        word_tts = story_download_from_openai(detail[0]["story_text"])
        if not word_tts:
            return ""
        upload_responce = upload_file_to_bucket(bucket_server, tts_path, word_tts, storage_client_service)
    tts_data = storage_client_service.storage.from_(bucket.id).download(tts_path)
    return tts_data

