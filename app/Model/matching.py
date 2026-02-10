"""
Modelační třídy pro hodnocení matching
"""
from pydantic import BaseModel, Field

class MatchingRatingWord(BaseModel):
    """
    Words in rating
    """
    matching_rating_word_id: str = Field(description="ID word PK")
    word_id: str = Field(description="Word ID in mathing")

class MatchingRating(BaseModel):
    """
    Rating
    """
    matching_rating_id: str = Field(description="ID word PK")
    click_counter: int = Field(description="Button click count")
    language_from: str = Field(description="From langugage")
    language_to: str = Field(description="To langugage")
    words: list[MatchingRatingWord] = Field(description="Words in matching")

