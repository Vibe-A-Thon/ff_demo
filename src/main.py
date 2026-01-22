from fastapi import FastAPI

app = FastAPI(title="Fraud Forge API")


@app.get("/")
def read_root():
    return {"message": "Welcome to Fraud Forge API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
