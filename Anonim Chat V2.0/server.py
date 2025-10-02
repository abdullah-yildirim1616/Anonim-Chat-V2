from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uuid
from typing import Dict, List

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Hafıza "veritabanı"
users: Dict[str, dict] = {}       # user_id -> {username, password}
waiting: List[str] = []           # bekleyen user_id listesi
rooms: Dict[str, List[str]] = {}  # room_id -> [user1, user2]
connections: Dict[str, WebSocket] = {}  # user_id -> WebSocket

ADMIN_PASSWORD = "1234"

# ----------------- Ana Sayfa -----------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ----------------- Kayıt -----------------
@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...)):
    user_id = str(uuid.uuid4())[:6]
    users[user_id] = {"username": username, "password": password}
    return HTMLResponse(f"<h2>Kayıt başarılı! User ID: {user_id}</h2><a href='/'>Ana Sayfa</a>")

# ----------------- Giriş -----------------
@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    for uid, info in users.items():
        if info["username"] == username and info["password"] == password:
            # Login başarılı → chat sayfasına yönlendir
            return RedirectResponse(url=f"/chat?user_id={uid}", status_code=303)
    return HTMLResponse("<h1>Geçersiz kullanıcı adı veya şifre</h1><a href='/'>Ana Sayfa</a>")

# ----------------- Chat Sayfası -----------------
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, user_id: str = Query(...)):
    if user_id not in users:
        return HTMLResponse("<h1>Geçersiz user_id</h1>")
    return templates.TemplateResponse("chat.html", {"request": request, "user_id": user_id})

# ----------------- Admin -----------------
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, password: str = Query(None)):
    if password != ADMIN_PASSWORD:
        return HTMLResponse("<h1>403 Forbidden</h1>", status_code=403)
    return templates.TemplateResponse("admin.html", {"request": request})

@app.post("/match")
async def match(password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return {"error": "Yetkisiz"}

    print("Waiting list before match:", waiting)
    matched = []
    while len(waiting) >= 2:
        user1 = waiting.pop(0)
        user2 = waiting.pop(0)
        room_id = str(uuid.uuid4())
        rooms[room_id] = [user1, user2]
        matched.append((user1, user2))
        print(f"Matched: {user1} - {user2}")

        if user1 in connections:
            await connections[user1].send_text(f"{user2} ile eşleştin.")
        if user2 in connections:
            await connections[user2].send_text(f"{user1} ile eşleştin.")
    print("Waiting list after match:", waiting)
    return {"matched": matched}

# ----------------- WebSocket -----------------
@app.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    connections[user_id] = websocket

    if user_id not in waiting:
        waiting.append(user_id)
        await websocket.send_text("Beklemeye alındın. Admin eşleştirecek.")

    try:
        while True:
            data = await websocket.receive_text()
            for room_id, users_in_room in rooms.items():
                if user_id in users_in_room:
                    partner = users_in_room[0] if users_in_room[1] == user_id else users_in_room[1]
                    if partner in connections:
                        await connections[partner].send_text(f"{users[user_id]['username']}: {data}")
    except WebSocketDisconnect:
        if user_id in waiting:
            waiting.remove(user_id)
        if user_id in connections:
            del connections[user_id]
