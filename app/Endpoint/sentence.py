from datetime import datetime
from uuid import uuid4
from app.Endpoint.openAI_client import openAIClient


class SentenceTense():
    id: str
    name_cz: str
    name_en: str

class SentenceKind():
    id: str
    name: str

class SenteceType():
    tense: SentenceTense

def allTenses(database_anon):
    tenses = database_anon.from_("tense_check_tense").select("*")
    try:
        tenses_data = tenses.execute()
    except Exception as e:
        raise Exception("Error in comunation with database")
    if len(tenses_data.data) > 0:
        tenses_data = tenses_data.data
    else:
        tenses_data = None
    return tenses_data

def check_tense(database_anon, tense):
    #sentence = database_anon.from_("tense_check_all_sentence").select("*")
    if tense:
        tense_data = database_anon.from_("tense_check_tense").select("*").ilike("text_eng", f"%{tense}%").execute()
        if len(tense_data.data) > 0:
            #tense = sentence.eq("tense_id", tense_data.data[0]["tense_check_tense_id"])
            return tense_data.data[0]["tense_check_tense_id"]
    return ""

def check_sentence_type(sentence_type):
    if sentence_type.upper() in ["POSITIVE","NEGATIVE","QUESTION"]:
        return sentence_type
    return ""
def random_sentence(database_anon, tense_id: str, sentence_type: str):
    sentence = database_anon.from_("tense_check_all_sentence").select("*")
    if tense_id:
        tense_id = check_tense(database_anon, tense_id)
        sentence = sentence.eq("tense_id", tense_id)
    if sentence_type:
        sentence_type = check_sentence_type(sentence_type)
        sentence = sentence.ilike("sentence_type", f"%{sentence_type}%")
    try:
        sentence_data = sentence.execute()
    except Exception as e:
        raise Exception("Error in comunation with database")
    sentence_responce = {"text_eng": ""}
    if datetime.now().second % 10 == 0: # len(sentence_data.data) > 20
        sentence_data = sentence_data.data[0]
        sentence_responce = sentence_data
        sentence_responce = {
            "text_eng": sentence_data["text_eng"],
            "text_cz": sentence_data["text_cz"],
            "tense_id": sentence_data["tense_id"],
            "sentence_type": sentence_data["sentence_type"]
        }
    else:
        # call OpenAI
        client = openAIClient()
        client.create_client()
        tense_db = database_anon.from_("tense_check_tense").select("*").eq("tense_check_tense_id", tense_id).execute()
        if len(tense_db.data) > 0:
            tense = tense_db.data[0]["text_eng"]
        else:
            tense = "Past simple"
        sentence = client.get_sentence_with_parameters(tense,sentence_type)
        if sentence.sentence_type == "affirmative":
            sentence.sentence_type = "positive"

        sentence_responce = {
            "text_eng": sentence.sentence,
            "text_cz": sentence.czech_translation,
            "tense_id": str(uuid4()),
            "sentence_type": sentence.sentence_type
        }
        new_sentence = {
            "tense_check_sentence_id": sentence_responce["tense_id"],
             "text_eng": sentence_responce["text_eng"], 
             "text_cz": sentence_responce["text_cz"],
             "tts_path_eng": "",
             "tts_path_cz": "",
             "sentence_type": sentence_responce["sentence_type"],
             "tense_id": check_tense(database_anon, sentence.tense)
            }
        sentence = database_anon.from_("tense_check_sentence").insert(new_sentence).execute()
        #sentence.phrasal_verb
        #sentence.word_count
    return sentence_responce
def check_change_sentence(database_anon, old_sentence, new_sentence, target_tense, target_sentence_type):
    client = openAIClient()
    client.create_client()
    return client.get_check_sentence(old_sentence, new_sentence, target_tense, target_sentence_type)
