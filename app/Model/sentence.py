"""
Modelační třídy pro věty
"""
from typing import Optional
from pydantic import BaseModel, Field

class SentenceType(BaseModel):
    Tense: str = Field(description="Tense of sentence (PAST/PRESENT/FUTURE)", default="")
    Type: str = Field(description="Type of sentence (POSITIVE/NEGATIVE/QUESTION)", default="")

class SentenceCheckAnswer(BaseModel):
    SourceSentence: str = Field(description="Source sentence")
    NewSentence: str = Field(description="New sentence to check")
    TargetTense: str = Field(description="Target tense")
    TargetTenseType: str = Field(description="Target tense type")
