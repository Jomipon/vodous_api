from uuid import uuid4
from app.Model.matching import MatchingRating

def matching_set_rating(rating: MatchingRating, database):
    """
    Rating for matching
    
    :param rating: JSON rating
    :type rating: MatchingRating
    :param database: Database connection
    """
    duplicate = database.from_("matching_rating").select("*").eq("matching_rating_id", rating.matching_rating_id).execute()
    if len(duplicate.data) > 0:
        rating.matching_rating_id = str(uuid4())

    matching_rating = {}
    matching_rating["matching_rating_id"] = rating.matching_rating_id
    matching_rating["click_counter"] = rating.click_counter
    matching_rating["language_from"] = rating.language_from
    matching_rating["language_to"] = rating.language_to
    words = []
    try:
        for word in rating.words:
            duplicate = database.from_("matching_rating_word").select("*").eq("matching_rating_word_id", word.matching_rating_word_id).execute()
            if len(duplicate.data) > 0:
                word.matching_rating_word_id = str(uuid4())
            words.append({"matching_rating_word_id": str(uuid4()), "matching_rating_id": matching_rating["matching_rating_id"], "word_id": word.word_id})
        database.from_("matching_rating").insert(matching_rating).execute()
        for word in words:
            database.from_("matching_rating_word").insert(word).execute()
        return {"status": "ok"}
    except:
        return {"status": "error"}