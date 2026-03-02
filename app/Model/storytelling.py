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

class StorytellingEvaluationStory(BaseModel):
    """
    Storyteling - Evaluation story
    """
    original: str = Field(description="Original text")
    student: str = Field(description="Student text")
