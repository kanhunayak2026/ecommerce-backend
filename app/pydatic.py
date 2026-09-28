from pydantic import BaseModel,Field,field_validator

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
    name: str= Field(min_length=1)
    description: str | None = None
    price: float =Field(gt=0)
    stock: int = Field(gt=0)
    category_id: int


class ProductUpdate(BaseModel):
    name: str
    description: str | None = None
    price: float= Field(gt=0)
    stock: int=Field(gt=0)
    category_id: int


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    stock: int
    category_id: int

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    name: str


class CategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int

    class Config:
        from_attributes = True