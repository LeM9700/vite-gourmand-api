from fastapi import FastAPI
from app.modules.menus.router import router as menus_router
from app.modules.auth.router import router as auth_router
from app.modules.orders.router import router as orders_router


app = FastAPI(title="Vite & Gourmand API")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(menus_router)
app.include_router(auth_router)
app.include_router(orders_router)