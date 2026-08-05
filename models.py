"""
MODELS MODULE (Pydantic)
Definisce la struttura tipizzata dei dati per la validazione automatica delle API.
"""
from pydantic import BaseModel
from typing import List

class SequenzaInput(BaseModel):
    id: str
    sequenza: str

class RichiestaAnalisi(BaseModel):
    modelloAI: str
    strumentoVienna: str
    sequenze: List[SequenzaInput]