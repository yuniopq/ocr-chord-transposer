from fastapi import FastAPI, UploadFile, File
import motor_acordes
from PIL import Image
import io

app = FastAPI()

@app.post("/analizar/")
async def analizar(file: UploadFile = File(...)):
    img = Image.open(io.BytesIO(await file.read())).convert("RGB")
    
    # Check Firebase first
    doc_ref = motor_acordes.db.collection("partituras").document(file.filename)
    doc = doc_ref.get()
    
    if doc.exists:
        return {"source": "firebase", "acordes": doc.to_dict()["acordes"]}
    
    # Run OCR
    acordes = motor_acordes.detectar_acordes_global(img)
    doc_ref.set({"acordes": acordes})
    return {"source": "ocr", "acordes": acordes}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
