from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserUpdate(BaseModel):
    name: str
    email: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    
    class Config:
            from_attributes = True
    

class UserLogin(BaseModel):
    email: str
    password: str

class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    stock: int


class ProductUpdate(BaseModel):
    name: str
    description: str | None = None
    price: float
    stock: int


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    stock: int

    class Config:
        from_attributes = True