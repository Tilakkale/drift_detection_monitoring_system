from fastapi import FastAPI

app = FastAPI(
    title="Data Drift Monitoring System",
    description="Industry Level ML Drift Monitoring Backend",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "message": "Data Drift Monitoring System Running"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }