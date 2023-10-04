from pydantic import BaseModel, Field
from typing import Union


class Inventario(BaseModel):
    nombre: str
    cantidad: int
    precio: float