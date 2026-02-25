from pydantic import BaseModel, Field

class envioInfo(BaseModel):
    category : str
    date : str
    mount : float
    description : str

class envioUsers(BaseModel):
    username : str
    email : str
    password : str

class editarUser(BaseModel):
    username : str
    email : str

class LoginRequest(BaseModel):
    email : str
    password : str 

class Cambiarcontra(BaseModel):
    actual : str
    nueva : str
    confirmar : str