from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Our synth CRM is runing now!"}

@app.get("/health")
def health():
    return {"status": "ok"}

