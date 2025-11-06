from fastapi import FastAPI

# Create FastAPI app
app = FastAPI(
    title="SmarTest API",
    description="AI Question Generation and Evaluation System",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "message": "SmarTest API is running!",
        "status": "success"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SmarTest Backend"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
