from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio

# --- Internal API Imports ---
from api.database import init_db, log_message, get_full_dashboard_data
from api.groq_processor import process_job_message
from api.broadcaster import broadcast_job

# 1. Initialize the FastAPI app FIRST
app = FastAPI()

# Create the Waiting Room (In-Memory Queue)
job_queue = asyncio.Queue()

# 2. Initialize SQLite Database & Start Queue Worker on startup
@app.on_event("startup")
async def on_startup():
    init_db()
    # Start the worker loop in the background the moment the server boots up
    asyncio.create_task(queue_worker())
    print("✅ System Online & Queue Worker Listening...")

# 3. Allow the frontend to access these APIs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Models ---
class IncomingMessage(BaseModel):
    source_type: str  
    platform: str     
    sender_name: str
    raw_text: str

# --- Dashboard API ---
@app.get("/api/dashboard")
def get_dashboard_data():
    """Grabs the live, formatted data directly from the SQLite database for the frontend"""
    return get_full_dashboard_data()

# --- Synchronous Processor ---
def process_and_forward(msg: IncomingMessage):
    """The heavy lifting (LLM & Broadcasting)"""
    print(f"⚙️ Processing job from {msg.sender_name}...")
    
    # 1. Process text through Groq LLM
    formatted_text = process_job_message(msg.raw_text)
    
    if "Error:" in formatted_text or not formatted_text:
        print("❌ Groq processing failed/rejected. Aborting forward.")
        return

    # 2. Broadcast directly to WhatsApp and Telegram
    print("✅ Formatting Passed. Broadcasting directly...")
    broadcast_job(formatted_text)

    # 3. Log the successful outgoing message to SQLite so the Dashboard sees it
    log_message(
        direction="outgoing", 
        source="System", 
        platform="broadcast", 
        name="All Channels", 
        full_text=formatted_text
    )
    print("✅ Job processed successfully.")

# --- The Queue Worker Loop ---
async def queue_worker():
    """This loop runs forever in the background, processing ONE job at a time."""
    while True:
        msg = await job_queue.get()
        
        try:
            await asyncio.to_thread(process_and_forward, msg)
            await asyncio.sleep(2) 
        except Exception as e:
            print(f"⚠️ Worker encountered an error: {e}")
        finally:
            job_queue.task_done()

# --- Webhook Listener ---
@app.post("/webhook/job")
async def handle_incoming_job(msg: IncomingMessage):
    
    log_message(
        direction="incoming", 
        source=msg.source_type, 
        platform=msg.platform, 
        name=msg.sender_name, 
        full_text=msg.raw_text
    )

    await job_queue.put(msg)
    
    return {
        "status": "queued", 
        "position_in_line": job_queue.qsize(), 
        "message": "Job added to queue."
    }