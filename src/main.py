from fastapi import FastAPI

app = FastAPI()


@app.get("/hello-world")
async def hello_world() -> str:
    return "Hello world..."
