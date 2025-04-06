from fastapi import FastAPI, Request
from pydantic import BaseModel, EmailStr
import asyncio
from email_generator import generate_email   # import your async main()

app = FastAPI()

class UserInput(BaseModel):
    name: str
    email: EmailStr
    phone: str
    query: str

@app.post("/generate-email")
async def generate_email(data: UserInput):
    print(data)
    try:
        result = await generate_email(data.name, data.email, data.phone, data.query)
        return {"status": "success", "email": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# asyncio.run(generate_email('John Doe','john_doe@gmail.com','+91 9111025593','How did you get started in this field, and what has your career path been like so far?'))
