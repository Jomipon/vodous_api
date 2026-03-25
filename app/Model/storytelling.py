"""
Modelační třídy pro storytelling
"""
from enum import Enum
from pydantic import BaseModel, Field

class TenseEnum(str, Enum):
    past = 'PAST'
    present = 'PRESENT'
    future = 'FUTURE'

class StorytellingStoryByTopic(BaseModel):
    """
    Storyteling - story by topic
    """
    topic: str = Field(description="Topic")
    tense: TenseEnum = Field(description="Tense for story (PAST,PRESENT,FUTURE)", )
    min_words: int = Field(description="Minimum of word count", default=140)
    max_words: int = Field(description="Maximum of word count", default=180)

class StorytellingEvaluationStory(BaseModel):
    """
    Storyteling - Evaluation story
    """
    original: str = Field(description="Original text")
    student: str = Field(description="Student text")
