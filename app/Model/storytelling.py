"""
Modelační třídy pro storytelling
"""
from pydantic import BaseModel, Field

class StorytellingStoryByTopic(BaseModel):
    """
    Storyteling - story by topic
    """
    topic: str = Field(description="Topic")

class StorytellingEvaluationStory(BaseModel):
    """
    Storyteling - Evaluation story
    """
    original: str = Field(description="Original text")
    student: str = Field(description="Student text")
