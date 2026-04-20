import os
import json
import asyncio
import csv
import io
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from core.extractor_service import ExtractorService

app = FastAPI(title="Web Extractor Pro")

# Create static directory if it doesn't exist
if not os.path.exists("static"):
    os.makedirs("static")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Shared storage for results (in-memory for local use)
latest_results = []

class ExtractRequest(BaseModel):
    urls: List[str]
    api_key: str
    model: str = "gemini/gemini-2.5-flash"

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("static/index.html", "r") as f:
        return f.read()

@app.post("/api/extract")
async def extract_contacts(req: ExtractRequest):
    global latest_results
    latest_results = [] # Clear previous results
    
    extractor = ExtractorService(req.api_key, model_id=req.model)
    
    async def event_generator():
        total = len(req.urls)
        for i, url in enumerate(req.urls, 1):
            # We wrap the generator in an async environment
            # Note: extractor.process_url_yield is a regular generator, 
            # we'll run it in a thread to keep FastAPI async loop free
            
            # Using a loop for the generator
            for event in extractor.process_url_yield(url, i, total):
                if event["type"] == "result":
                    latest_results.append(event["data"])
                
                yield f"data: {json.dumps(event)}\n\n"
                await asyncio.sleep(0.1) # Small pause for UI smoothness
        
        yield "data: {\"type\": \"complete\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/download")
async def download_results():
    if not latest_results:
        return {"error": "No results to download"}
    
    output = io.StringIO()
    fieldnames = [
        "url", "business_name", "owner_name", "emails", "phones", "address", "facebook_url", "linkedin_url"
    ]
    
    # Flatten results for CSV
    flat_results = []
    for r in latest_results:
        flat = dict(r)
        flat["emails"] = ", ".join(r.get("emails") or [])
        flat["phones"] = ", ".join(r.get("phones") or [])
        flat_results.append(flat)
        
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(flat_results)
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=extracted_contacts.csv"}
    )

if __name__ == "__main__":
    import uvicorn
    # Use the specific python path if running directly
    uvicorn.run(app, host="0.0.0.0", port=8000)
