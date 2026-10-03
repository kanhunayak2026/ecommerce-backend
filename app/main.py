from fastapi import FastAPI, Depends,HTTPException,Query
from sqlalchemy.orm import Session
import bcrypt
from typing import Literal
from app.redis_client import redis_client
import json

from app.database import engine, SessionLocal
from app.model import Base, User
from app.pydatic import (
     UserCreate, UserUpdate, UserLogin, UserResponse,
    ProductCreate, ProductUpdate, ProductResponse,
    CategoryCreate, CategoryUpdate, CategoryResponse,
    CartItemCreate,CartItemUpdate,CartItemResponse,
    OrderResponse,OrderStatusUpdate

)

from app.auth import create_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth import verify_token
from app.product_model import Product
from app.category_model import Category
from app import cart_model
from app.cart_model import Cart, CartItem
from app import order_model
from app.order_model import Order, OrderItem
from app.cart_model import Cart, CartItem

app = FastAPI()
def clear_product_cache():
    keys = redis_client.keys("products:*")

    if keys:
        redis_client.delete(*keys)
security = HTTPBearer()
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    user_id = verify_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return user_id

def get_admin_user(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return user



@app.get("/")
def home():
    return {"message": "E-Commerce Backend is running"}


@app.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
     # Check if email already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    password_hash = bcrypt.hashpw(
        user_data.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

# GET ALL USERS
@app.get("/users", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    users = db.query(User).all()

    return users

#get a specific user
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return {"message": "User not found"}

    return user
#delete a user
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return {"message": "User not found"}

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return {"message": "User not found"}

    user.name = user_data.name
    user.email = user_data.email

    db.commit()
    db.refresh(user)

    return user

#login api
@app.post("/login")
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    password_valid = bcrypt.checkpw(
        user_data.password.encode("utf-8"),
        user.password_hash.encode("utf-8")
    )

    if not password_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    access_token = create_access_token(user.id,user.role)
    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer"

    }

@app.get("/admin")
def admin_dashboard(
    user: User = Depends(get_admin_user)
):
    return {
        "message": "Welcome Admin",
        "user_id": user.id,
        "role": user.role
    }

# CREATE PRODUCT - ADMIN ONLY
@app.post("/products", response_model=ProductResponse)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    category = db.query(Category).filter(
    Category.id == product_data.category_id
    ).first()

    if not category:
     raise HTTPException(
        status_code=400,
        detail="Category not found"
    )
    product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock=product_data.stock,
        category_id=product_data.category_id
    )

    db.add(product)
    db.commit()
    db.refresh(product)
    clear_product_cache()

    return product


# GET ALL PRODUCTS - AUTHENTICATED USERS
@app.get("/products", response_model=list[ProductResponse])
def get_products(
    search: str | None = None,
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort_by: Literal["price", "name", "stock", "id"] | None = None,
    order: Literal["asc", "desc"] = "asc",
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    # Create a unique cache key based on the request parameters
    cache_key = (
        f"products:"
        f"search={search}:"
        f"category={category_id}:"
        f"min={min_price}:"
        f"max={max_price}:"
        f"sort={sort_by}:"
        f"order={order}:"
        f"page={page}:"
        f"limit={limit}"
    )

    # 1. Check Redis
    cached_products = redis_client.get(cache_key)

    if cached_products:
        return json.loads(cached_products)

    # 2. If not in Redis, query MySQL
    query = db.query(Product)

    if search:
        query = query.filter(
            Product.name.ilike(f"%{search}%")
        )

    if category_id:
        query = query.filter(
            Product.category_id == category_id
        )

    if min_price is not None:
        query = query.filter(
            Product.price >= min_price
        )

    if max_price is not None:
        query = query.filter(
            Product.price <= max_price
        )

    # 3. Sorting
    sort_fields = {
        "price": Product.price,
        "name": Product.name,
        "stock": Product.stock,
        "id": Product.id
    }

    if sort_by in sort_fields:
        column = sort_fields[sort_by]

        if order == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    # 4. Pagination
    offset = (page - 1) * limit

    query = query.offset(offset).limit(limit)

    products = query.all()

    # 5. Convert products to JSON-compatible data
    product_data = [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "category_id": product.category_id
        }
        for product in products
    ]

    # 6. Store result in Redis for 60 seconds
    redis_client.setex(
        cache_key,
        120,
        json.dumps(product_data)
    )

    # 7. Return data
    return product_data

# GET ONE PRODUCT - AUTHENTICATED USERS
@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# UPDATE PRODUCT - ADMIN ONLY
@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    category = db.query(Category).filter(
     Category.id == product_data.category_id
    ).first()

    if not category:
     raise HTTPException(
        status_code=400,
        detail="Category not found"
    )
    product.name = product_data.name
    product.description = product_data.description
    product.price = product_data.price
    product.stock = product_data.stock
    product.category_id = product_data.category_id

    db.commit()
    db.refresh(product)
    clear_product_cache()

    return product


# DELETE PRODUCT - ADMIN ONLY
@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }

@app.post("/categories", response_model=CategoryResponse)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    existing_category = db.query(Category).filter(
        Category.name == category_data.name
    ).first()

    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Category already exists"
        )

    category = Category(
        name=category_data.name
    )

    db.add(category)
    db.commit()
    db.refresh(category)
    clear_product_cache()

    return category

@app.get("/categories", response_model=list[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    return db.query(Category).all()


@app.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    category = db.query(Category).filter(
        Category.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    return category

@app.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    category = db.query(Category).filter(
        Category.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    category.name = category_data.name

    db.commit()
    db.refresh(category)

    return category


@app.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    category = db.query(Category).filter(
        Category.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    db.delete(category)
    db.commit()

    return {"message": "Category deleted successfully"}


@app.post("/cart/items", response_model=CartItemResponse)
def add_to_cart(
    cart_item: CartItemCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    # Check product exists
    product = db.query(Product).filter(
        Product.id == cart_item.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Find user's cart
    cart = db.query(Cart).filter(
        Cart.user_id == user_id
    ).first()

    # Create cart if it doesn't exist
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    # Check if product is already in cart
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == cart_item.product_id
    ).first()

    if existing_item:
        existing_item.quantity += cart_item.quantity
    else:
        existing_item = CartItem(
            cart_id=cart.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity
        )
        db.add(existing_item)

    db.commit()
    db.refresh(existing_item)

    return existing_item

@app.get("/cart", response_model=list[CartItemResponse])
def get_cart(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    cart = db.query(Cart).filter(
        Cart.user_id == user_id
    ).first()

    if not cart:
        return []

    cart_items = db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).all()

    return cart_items

@app.delete("/cart/items/{item_id}")
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    cart = db.query(Cart).filter(
        Cart.user_id == user_id
    ).first()

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    db.delete(item)
    db.commit()

    return {"message": "Cart item removed successfully"}
@app.put("/cart/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(
    item_id: int,
    cart_item: CartItemUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    cart = db.query(Cart).filter(
        Cart.user_id == user_id
    ).first()

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    item.quantity = cart_item.quantity

    db.commit()
    db.refresh(item)

    return item

@app.delete("/cart")
def clear_cart(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    cart = db.query(Cart).filter(
        Cart.user_id == user_id
    ).first()

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).delete(synchronize_session=False)

    db.commit()

    return {"message": "Cart cleared successfully"}

@app.post("/orders", response_model=OrderResponse)
def create_order(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    # Find user's cart
    cart = db.query(Cart).filter(
        Cart.user_id == user_id
    ).first()

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    # Get cart items
    cart_items = db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).all()

    if not cart_items:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    # Check products and stock
    total_amount = 0

    for item in cart_items:
        product = db.query(Product).filter(
            Product.id == item.product_id
        ).first()

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found"
            )

        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product.name}"
            )

        total_amount += product.price * item.quantity

    # Create order
    order = Order(
        user_id=user_id,
        total_amount=total_amount,
        status="pending"
    )

    db.add(order)
    db.flush()

    # Create order items and reduce stock
    for item in cart_items:
        product = db.query(Product).filter(
            Product.id == item.product_id
        ).first()

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity,
            price=product.price
        )

        db.add(order_item)

        product.stock -= item.quantity

    # Clear cart
    db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).delete(synchronize_session=False)

    db.commit()
    db.refresh(order)

    order_items = db.query(OrderItem).filter(
    OrderItem.order_id == order.id
).all()

    return {
     "id": order.id,
     "total_amount": order.total_amount,
     "status": order.status,
     "items": order_items
    }

@app.get("/orders", response_model=list[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    orders = db.query(Order).filter(
        Order.user_id == user_id
    ).all()

    result = []

    for order in orders:
        items = db.query(OrderItem).filter(
            OrderItem.order_id == order.id
        ).all()

        result.append({
            "id": order.id,
            "total_amount": order.total_amount,
            "status": order.status,
            "items": items
        })

    return result

@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    items = db.query(OrderItem).filter(
        OrderItem.order_id == order.id
    ).all()

    return {
        "id": order.id,
        "total_amount": order.total_amount,
        "status": order.status,
        "items": items
    }

@app.put("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    order = db.query(Order).filter(
        Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    order.status = status_data.status

    db.commit()
    db.refresh(order)

    items = db.query(OrderItem).filter(
        OrderItem.order_id == order.id
    ).all()

    return {
        "id": order.id,
        "total_amount": order.total_amount,
        "status": order.status,
        "items": items
    }
@app.put("/orders/{order_id}/cancel", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending orders can be cancelled"
        )

    # Get order items
    order_items = db.query(OrderItem).filter(
        OrderItem.order_id == order.id
    ).all()

    # Restore product stock
    for item in order_items:
        product = db.query(Product).filter(
            Product.id == item.product_id
        ).first()

        if product:
            product.stock += item.quantity

    # Cancel order
    order.status = "cancelled"

    db.commit()
    db.refresh(order)

    return {
        "id": order.id,
        "total_amount": order.total_amount,
        "status": order.status,
        "items": order_items
    }