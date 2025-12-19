import random
import secrets

from fastapi import (Depends, FastAPI, Form, HTTPException, Request, Response,
                     status)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer
from models import ClothingItem, User
from pydantic import BaseModel
from schemas import ItemCreate, ItemUpdate
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Secret key for signing session cookies
SECRET_KEY = secrets.token_hex(32)
serializer = URLSafeTimedSerializer(SECRET_KEY)

engine = create_engine("sqlite:///database.db")


def get_db():
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
    db = next(get_db())

    if not db.exec(select(User).where(User.username == "alice")).first():
        alice = User(username="alice", password="password123",
                     name="Alice Johnson", email="alice@example.com")
        db.add(alice)
        db.commit()
        db.refresh(alice)

        db.add(ClothingItem(name="Blue Jeans", category="bottoms", color="blue",
               season="all", notes="Favorite pair of jeans.", user_id=alice.id))
        db.add(ClothingItem(name="Red T-Shirt", category="tops",
               color="red", season="summer", notes="", user_id=alice.id))
        db.commit()
    if not db.exec(select(User).where(User.username == "bob")).first():
        bob = User(username="bob", password="password456",
                   name="Bob Smith", email="bob@example.com")
        db.add(bob)
        db.commit()


def create_session_token(username: str) -> str:
    """Create a secure session token for a user"""
    return serializer.dumps(username)


def verify_session_token(token: str) -> str | None:
    """Verify a session token and return the username"""
    try:
        # Token expires after 1 day (86400 seconds)
        username = serializer.loads(token, max_age=86400)
        return username
    except:
        return None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Get the currently logged-in user from the session cookie"""
    session_token = request.cookies.get("session")
    if not session_token:
        return None

    username = verify_session_token(session_token)
    if not username:
        return None
    return db.exec(select(User).where(User.username == username)).first()


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_302_FOUND,
                            headers={"Location": "/login"})
    return user


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Home page - redirects based on login status"""
    user = get_current_user(request, db)

    if user:
        # User is logged in, redirect to dashboard
        return RedirectResponse(url="/wardrobe", status_code=status.HTTP_302_FOUND)
    else:
        # User is not logged in, show login page
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    """Show the login page"""
    user = get_current_user(request, db)

    # If already logged in, redirect to dashboard
    if user:
        return RedirectResponse(url="/wardrobe", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("login.html", {
        "request": request
    })


@app.post("/login", response_class=HTMLResponse)
async def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if user exists and password matches
    user = db.exec(select(User).where(User.username == username)).first()
    if not user or user.password != password:
        # Login failed - return error fragment
        return """
        <div id="login-error" class="error-message">
            ❌ Invalid username or password
        </div>
        """

    # Login successful - create session token
    session_token = create_session_token(username)

    # Return success message with redirect instruction
    response = HTMLResponse("""
        <div class="success-message">
            ✅ Login successful! Redirecting...
        </div>
        <script>
            setTimeout(() => window.location.href = '/wardrobe', 1000);
        </script>
    """)

    # Set the session cookie
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,  # Can't be accessed by JavaScript
        secure=False,   # Set to True in production with HTTPS
        samesite="lax"  # CSRF protection
    )

    return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle registration form submission"""
    if db.exec(select(User).where(User.username == username)).first():
        return HTMLResponse('<div id="register-error" class="error-message">❌ Username already exists</div>')
    user = User(username=username, password=password, name=name, email=email)
    db.add(user)
    db.commit()
    session_token = create_session_token(username)
    response = HTMLResponse("""
        <div class="success-message">✅ Registration successful! Redirecting to wardrobe...</div>
        <script>setTimeout(() => window.location.href = '/wardrobe', 1000);</script>
    """)
    response.set_cookie(key="session", value=session_token,
                        httponly=True, secure=False, samesite="lax")
    return response


@app.post("/logout", response_class=HTMLResponse)
async def logout():
    """Handle logout"""
    response = RedirectResponse(
        url="/login", status_code=status.HTTP_302_FOUND)

    # Delete the session cookie
    response.delete_cookie("session")

    return response

# wardrobe routes


@app.get("/wardrobe", response_class=HTMLResponse)
async def wardrobe_page(request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)):
    items = db.exec(select(ClothingItem).where(
        ClothingItem.user_id == user.id)).all()
    return templates.TemplateResponse("wardrobe.html", {
        "request": request,
        "user": user,
        "items": items
    })


@app.post("/add-item", response_class=HTMLResponse)
async def add_item(item: ItemCreate = Form(...),
                   user: User = Depends(require_user),
                   db: Session = Depends(get_db)):
    item_data = item.dict()
    item_data['category'] = item_data['category'].strip().lower()
    item_data['color'] = item_data['color'].strip().lower()
    item_data['season'] = item_data['season'].strip().lower()
    new_item = ClothingItem(**item_data, user_id=user.id)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    items = db.exec(select(ClothingItem).where(
        ClothingItem.user_id == user.id)).all()
    html = templates.get_template(
        "fragments/wardrobe_grid.html").render(items=items)
    return HTMLResponse(f'{html}<span id="item-count" hx-swap-oob="true">{len(items)}</span>')


@app.post("/update-item", response_class=HTMLResponse)
async def update_item_endpoint(item_id: int = Form(...), item: ItemUpdate = Form(...), user: User = Depends(require_user), db: Session = Depends(get_db)):
    existing_item = db.get(ClothingItem, item_id)
    if not existing_item or existing_item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Item not found")
    item_data = item.dict(exclude_unset=True)
    for key, value in item_data.items():
        setattr(existing_item, key, value)
    db.add(existing_item)
    db.commit()
    db.refresh(existing_item)
    items = db.exec(select(ClothingItem).where(
        ClothingItem.user_id == user.id)).all()
    html = templates.get_template(
        "fragments/wardrobe_grid.html").render(items=items)
    return HTMLResponse(f'{html}<span id="item-count" hx-swap-oob="true">{len(items)}</span>')


@app.delete("/delete-item/{item_id}", response_class=HTMLResponse)
async def delete_item_endpoint(item_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    item = db.get(ClothingItem, item_id)
    if not item or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    items = db.exec(select(ClothingItem).where(
        ClothingItem.user_id == user.id)).all()
    return HTMLResponse(f'<span id="item-count" hx-swap-oob="true">{len(items)}</span>')


@app.get("/filter-items", response_class=HTMLResponse)
async def filter_items_endpoint(category: str | None = None, color: str | None = None, season: str | None = None, user: User = Depends(require_user), db: Session = Depends(get_db)):
    stmt = select(ClothingItem).where(ClothingItem.user_id == user.id)
    if category and category != "all":
        stmt = stmt.where(ClothingItem.category == category)
    if color and color != "all":
        stmt = stmt.where(ClothingItem.color == color)
    if season and season != "all":
        stmt = stmt.where(ClothingItem.season == season)
    items = db.exec(stmt).all()
    html = templates.get_template(
        "fragments/wardrobe_grid.html").render(items=items)
    return HTMLResponse(html)


@app.get("/generate-outfit", response_class=HTMLResponse)
async def generate_outfit(user: User = Depends(require_user), db: Session = Depends(get_db)):
    items = db.exec(select(ClothingItem).where(
        ClothingItem.user_id == user.id)).all()
    if len(items) < 2:
        return HTMLResponse('<div class="outfit-result"><p class="error-message">Add at least 2 items to generate an outfit!</p></div>')
    outfit_size = min(3, len(items))
    outfit = random.sample(items, outfit_size)
    html = '<div class="outfit-result"><h3>✨ Your Outfit Suggestion</h3><div class="outfit-items">'
    for item in outfit:
        html += f'<div class="outfit-item"><h4>{item.name}</h4><p><span class="badge">{item.category}</span></p></div>'
    html += '</div><p class="outfit-tip">💡 Mix and match these items for a great look!</p></div>'
    return HTMLResponse(html)


@app.get("/api/items")
async def api_get_items(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return {"error": "Unauthorized", "items": []}
    items = db.exec(select(ClothingItem).where(
        ClothingItem.user_id == user.id)).all()
    return {"username": user.username, "item_count": len(items), "items": [item.dict() for item in items]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
