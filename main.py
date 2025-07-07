from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from manim_renderer import render_and_upload_video, get_video_info
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Manim Video Generator API", version="1.0.0")

load_dotenv()

# Supabase client initialization
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class PromptRequest(BaseModel):
    prompt: str
    quality: str = "low"  # low, medium, high
    max_retries: int = 5

class VideoResponse(BaseModel):
    message: str
    task_id: str
    estimated_time: str = "2-5 minutes"

class VideoStatusResponse(BaseModel):
    task_id: str
    status: str  # processing, completed, failed, not_found
    video_url: str = None
    error_message: str = None
    attempts: int = None
    progress: str = None

@app.get("/")
async def root():
    return {
        "message": "Manim Video Generator API", 
        "version": "1.0.0",
        "endpoints": {
            "generate": "/generate-video/",
            "status": "/video-status/{task_id}",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Supabase connection
        result = supabase.table("videos").select("count").limit(1).execute()
        return {"status": "healthy", "supabase": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@app.post("/generate-video/", response_model=VideoResponse)
async def generate_video(request: PromptRequest, background_tasks: BackgroundTasks):
    """
    Generate a Manim animation video from a text prompt
    """
    try:
        # Validate input
        if not request.prompt or len(request.prompt.strip()) < 5:
            raise HTTPException(status_code=400, detail="Prompt must be at least 5 characters long")
        
        if request.max_retries < 1 or request.max_retries > 10:
            raise HTTPException(status_code=400, detail="max_retries must be between 1 and 10")
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        logger.info(f"Starting video generation for task {task_id} with prompt: {request.prompt[:100]}...")
        
        # Initialize database record
        supabase.table("videos").insert({
            "task_id": task_id,
            "prompt": request.prompt,
            "status": "queued",
            "quality": request.quality,
            "max_retries": request.max_retries,
            "video_url": None
        }).execute()
        
        # Start background task
        background_tasks.add_task(
            render_and_upload_video, 
            request.prompt, 
            supabase, 
            task_id, 
            request.max_retries
        )
        
        # Estimate completion time based on quality
        time_estimates = {
            "low": "1-3 minutes",
            "medium": "3-7 minutes", 
            "high": "5-15 minutes"
        }
        
        return VideoResponse(
            message="Video generation started successfully",
            task_id=task_id,
            estimated_time=time_estimates.get(request.quality, "2-5 minutes")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting video generation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/video-status/{task_id}", response_model=VideoStatusResponse)
async def get_video_status(task_id: str):
    """
    Get the status of a video generation task
    """
    try:
        # Validate task_id format
        try:
            uuid.UUID(task_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid task_id format")
        
        # Get video info from database
        video_info = get_video_info(task_id, supabase)
        
        if video_info.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Map database status to response
        status = video_info.get("status", "unknown")
        progress_messages = {
            "queued": "Task queued for processing",
            "processing": "Generating animation code and rendering video",
            "completed": "Video generation completed successfully",
            "failed": "Video generation failed"
        }
        
        return VideoStatusResponse(
            task_id=task_id,
            status=status,
            video_url=video_info.get("video_url"),
            error_message=video_info.get("error_message"),
            attempts=video_info.get("attempts"),
            progress=progress_messages.get(status, "Unknown status")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/video-info/{task_id}")
async def get_detailed_video_info(task_id: str):
    """
    Get detailed information about a video generation task (for debugging)
    """
    try:
        # Validate task_id format
        try:
            uuid.UUID(task_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid task_id format")
        
        video_info = get_video_info(task_id, supabase)
        
        if video_info.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Return detailed information (be careful about exposing sensitive data)
        return {
            "task_id": video_info.get("task_id"),
            "prompt": video_info.get("prompt"),
            "status": video_info.get("status"),
            "video_url": video_info.get("video_url"),
            "quality": video_info.get("quality"),
            "attempts": video_info.get("attempts"),
            "max_retries": video_info.get("max_retries"),
            "created_at": video_info.get("created_at"),
            "updated_at": video_info.get("updated_at"),
            "error_message": video_info.get("error_message"),
            # Don't expose the actual code for security reasons
            "has_final_code": bool(video_info.get("final_code"))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting detailed video info: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Legacy endpoint for backward compatibility
@app.get("/video-url/{task_id}")
async def get_video_url_legacy(task_id: str):
    """Legacy endpoint - use /video-status/{task_id} instead"""
    try:
        status_response = await get_video_status(task_id)
        
        if status_response.status == "completed":
            return {"status": "completed", "video_url": status_response.video_url}
        elif status_response.status == "failed":
            return {"status": "failed", "video_url": None, "error": status_response.error_message}
        else:
            return {"status": "processing", "video_url": None}
            
    except HTTPException as e:
        if e.status_code == 404:
            return {"status": "not_found", "video_url": None}
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")