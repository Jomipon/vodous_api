"""
Modelační třídy pro partnera
"""
from typing import Optional
from pydantic import BaseModel, Field

class WordContentIn(BaseModel):
    """
    Word - incoming
    """
    word_id_from: str = Field(description="[from]ID word PK")
    word_content_from: str = Field(description="[from]Content of word")
    word_language_from: str = Field(description="[from]Language of word")
    valid_from: bool = Field(description="[from]Word is valid")
    note_from: Optional[str] = Field(description="[from]Description")
    word_id_to: Optional[str] = Field(description="[to]ID word PK")
    word_content_to: Optional[str] = Field(description="[to]Content of word")
    word_language_to: Optional[str] = Field(description="[to]Language of word")
    valid_to: Optional[bool] = Field(description="[to]Word is valid")
    note_to: Optional[str] = Field(description="[to]Description")

class WordTranslateIn(BaseModel):
    """
    Translate of word - incoming
    """
    word_translate_id: str = Field(description="ID translate word PK")
    word_cz_id: str = Field(description="ID for CZ translate FK")
    word_en_id: str = Field(description="ID for EN translate FK")
    valid: bool = Field(description="Transleate is valid", default=False)
    note: str = Field(description="Description", default=False)

class WordContentTranslateOut(BaseModel):
    """
    Word translate - out
    """
    word_id: str = Field(description="ID translate word PK")
    word_content: str = Field(description="Content of word")
    word_language: str = Field(description="Language of word")
    valid: bool = Field(description="Word is valid")
    note: Optional[str] = Field(description="Description")

class WordContentOut(BaseModel):
    """
    Word - out
    """
    word_id: str = Field(description="ID word PK")
    word_content: str = Field(description="Content of word")
    word_language: str = Field(description="Language of word")
    valid: bool = Field(description="Word is valid")
    note: Optional[str] = Field(description="Description")
    translate: list[WordContentTranslateOut]


class EnvelopeWordContentOut(BaseModel):
    """
    Responce all word - out
    """
    status: str = Field(description="Return staus")
    data: Optional[list[WordContentOut]]

class WordSpeechOut(BaseModel):
    """
    Infromation about word and TTS
    """
    word_id: str = Field(description="ID Word")
    speech: bytes = Field(description="Audio")
class EnvelopeWordSpeechOut(BaseModel):
    """
    Responce class for word and audio TTS
    """
    status: str = Field(description="Return staus")
    data: Optional[list[WordSpeechOut]]
class EnvelopeWordRating(BaseModel):
    """
    Responce for translate rating
    """
    status: str = Field(description="Return staus")
class WordLanguageInfo(BaseModel):
    """
    Information about support language
    """
    word_language_from: str = Field("Language from")
    word_language_to: str = Field("Language fto")
class EnvelopeWordAllLanguages(BaseModel):
    """
    Responce class for all supported languages
    """
    status: str = Field(description="Return staus")
    #data: Optional[list[WordLanguageInfo]]
