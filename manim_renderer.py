import tempfile
import subprocess
import os
import traceback
from supabase import Client
from llm_utils import (
    enhance_prompt_and_generate_code, 
    fix_manim_code_with_error,
    extract_scene_name_from_code,
    validate_manim_code
)
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# def render_and_upload_video(prompt: str, supabase: Client, task_id: str, max_retries: int = 5):
#     """
#     Enhanced video rendering with better error handling and structured LLM communication
#     """
#     last_error = None
#     manim_code = None
#     fix_explanation = ""
    
#     try:
#         # Update status to processing
#         supabase.table("videos").upsert({
#             "task_id": task_id,
#             "status": "processing",
#             "video_url": None
#         }).execute()
        
#         for attempt in range(1, max_retries + 1):
#             logger.info(f"Attempt {attempt}/{max_retries} for task {task_id}")
            
#             try:
#                 # Generate or fix Manim code
#                 if attempt == 1:
#                     logger.info("Generating initial Manim code...")
#                     manim_code, explanation = enhance_prompt_and_generate_code(prompt)
#                     logger.info(f"Code generation explanation: {explanation}")
#                 else:
#                     logger.info(f"Fixing code based on error from attempt {attempt-1}...")
#                     # Create detailed error message for LLM
#                     error_details = format_error_for_llm(last_error, manim_code)
#                     manim_code, fix_explanation = fix_manim_code_with_error(
#                         manim_code or "", 
#                         error_details, 
#                         attempt
#                     )
#                     logger.info(f"Fix explanation: {fix_explanation}")
                
#                 # Validate code structure before attempting to render
#                 is_valid, validation_msg = validate_manim_code(manim_code)
#                 if not is_valid:
#                     logger.warning(f"Code validation failed: {validation_msg}")
#                     # Continue anyway, but log the warning
                
#                 logger.info(f"Generated/Fixed Manim code:\n{manim_code[:500]}...")
                
#                 # Attempt to render the video
#                 video_path = render_manim_video(manim_code, task_id)
                
#                 # If we get here, rendering was successful
#                 logger.info("Manim rendering successful!")
                
#                 # Upload to Supabase
#                 public_url = upload_video_to_supabase(video_path, task_id, supabase)
                
#                 # Update database with success
#                 supabase.table("videos").upsert({
#                     "task_id": task_id,
#                     "video_url": public_url,
#                     "status": "completed",
#                     "attempts": attempt,
#                     "final_code": manim_code
#                 }).execute()
                
#                 logger.info(f"Video successfully uploaded: {public_url}")
#                 return public_url
                
#             except subprocess.CalledProcessError as e:
#                 last_error = e
#                 stderr_output = e.stderr if isinstance(e.stderr, str) else e.stderr.decode()
#                 error_msg = f"Manim subprocess error: {stderr_output}"
#                 logger.error(f"Attempt {attempt} failed with subprocess error: {error_msg}")
                
#                 if attempt == max_retries:
#                     raise Exception(f"Failed to render after {max_retries} attempts. Last error: {error_msg}")
                    
#             except Exception as e:
#                 last_error = e
#                 logger.error(f"Attempt {attempt} failed with error: {str(e)}")
                
#                 if attempt == max_retries:
#                     raise Exception(f"Failed to render after {max_retries} attempts. Last error: {str(e)}")
    
#     except Exception as e:
#         logger.error(f"Fatal error in render_and_upload_video: {str(e)}")
#         # Update database with error status
#         supabase.table("videos").upsert({
#             "task_id": task_id,
#             "status": "failed",
#             "error_message": str(e),
#             "video_url": None
#         }).execute()
#         raise


import logging
import subprocess
from typing import Tuple
from supabase import Client

# Assume client, models, system prompts, and other helper functions are defined elsewhere
# (e.g., render_manim_video, upload_video_to_supabase, validate_manim_code, etc.)
logger = logging.getLogger(__name__)


def render_and_upload_video(prompt: str, supabase: Client, task_id: str, max_retries: int = 5):
    """
    Renders a Manim video with a robust retry and self-correction loop.
    A successful render immediately uploads the video, updates the database, and exits.
    """
    last_error = None
    manim_code = None
    
    # Initial status update
    try:
        supabase.table("videos").upsert({
            "task_id": task_id,
            "status": "processing",
            "video_url": None,
            "attempts": 0,
            "error_message": None,
        }).execute()
    except Exception as db_error:
        logger.error(f"Initial DB update failed for task {task_id}: {db_error}")
        # Depending on requirements, you might want to stop here
        # raise db_error 

    for attempt in range(1, max_retries + 1):
        logger.info(f"Attempt {attempt}/{max_retries} for task {task_id}")
        
        try:
            # Step 1: Generate or fix Manim code
            if attempt == 1:
                logger.info("Generating initial Manim code...")
                manim_code, explanation = enhance_prompt_and_generate_code(prompt)
                logger.info(f"Code generation explanation: {explanation}")
            else:
                logger.info(f"Fixing code based on error from attempt {attempt - 1}...")
                # Format the last known error for the LLM
                error_details = format_error_for_llm(last_error, manim_code) # type: ignore
                manim_code, fix_explanation = fix_manim_code_with_error(
                    manim_code or "", 
                    error_details, 
                    attempt
                )
                logger.info(f"Fix explanation: {fix_explanation}")
            
            # Optional: Validate code structure before rendering
            is_valid, validation_msg = validate_manim_code(manim_code)
            if not is_valid:
                logger.warning(f"Generated code validation failed: {validation_msg}")
            
            logger.info("Attempting to render the video...")
            
            # Step 2: Render the video
            video_path = render_manim_video(manim_code, task_id)
            
            # 💡 SUCCESS! If we get here, rendering worked.
            # The success logic is now INSIDE the loop's try block.
            logger.info("Manim rendering successful!")
            
            # Step 3: Upload the successful video
            public_url = upload_video_to_supabase(video_path, task_id, supabase)
            
            # Step 4: Update database with 'completed' status
            supabase.table("videos").upsert({
                "task_id": task_id,
                "video_url": public_url,
                "status": "completed",
                "attempts": attempt,
                "final_code": manim_code,
                "error_message": None # Clear any previous error messages
            }).execute()
            
            logger.info(f"Task {task_id} completed and video uploaded: {public_url}")
            
            # Step 5: Return the URL and exit the function entirely
            return public_url
            
        except subprocess.CalledProcessError as e:
            last_error = e
            
            # Check if stderr is bytes before decoding, otherwise use it directly.
            if e.stderr:
                stderr_output = e.stderr.decode(errors='ignore') if isinstance(e.stderr, bytes) else e.stderr
            else:
                stderr_output = "No stderr output."
                
            error_msg = f"Manim subprocess error: {stderr_output}"
            logger.error(f"Attempt {attempt} failed with subprocess error: {error_msg}")
        except Exception as e:
            last_error = e
            error_msg = f"An unexpected error occurred: {str(e)}"
            logger.error(f"Attempt {attempt} failed with error: {error_msg}")

        # If the loop continues, update the status with the latest error
        supabase.table("videos").upsert({
            "task_id": task_id,
            "status": "processing",
            "attempts": attempt,
            "error_message": error_msg
        }).execute()

    # If the loop completes without a successful return, it means all retries have failed.
    final_error_message = f"Failed to render video for task {task_id} after {max_retries} attempts."
    logger.error(final_error_message)
    
    # Final update to the database to mark as 'failed'
    supabase.table("videos").upsert({
        "task_id": task_id,
        "status": "failed",
        "error_message": str(last_error), # Store the last captured error
        "video_url": None
    }).execute()
    
    # Raise an exception to signify failure to the caller
    raise Exception(final_error_message)


def format_error_for_llm(error: Exception, code: str) -> str:
    """
    Format error information in a structured way for the LLM to understand
    """
    if isinstance(error, subprocess.CalledProcessError):
        # Get stderr if available
        stderr_output = error.stderr.decode() if error.stderr else "No stderr available"
        stdout_output = error.stdout.decode() if error.stdout else "No stdout available"
        
        return f"""MANIM SUBPROCESS ERROR:
Return Code: {error.returncode}
Command: {' '.join(error.cmd)}

STDERR OUTPUT:
{stderr_output}

STDOUT OUTPUT:
{stdout_output}

This error occurred when trying to execute the manim command to render the animation.
Common issues include:
- Syntax errors in Python code
- Missing imports
- Incorrect Manim object usage
- Scene class or construct method issues
- Object positioning or animation errors
"""
    else:
        # General Python exception
        return f"""PYTHON EXECUTION ERROR:
Error Type: {type(error).__name__}
Error Message: {str(error)}

Traceback:
{traceback.format_exc()}

This error occurred during code execution or preparation.
"""


def render_manim_video(manim_code: str, task_id: str) -> str:
    """
    Render Manim video and return the path to the generated video file
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write the code to a file
        file_name = f"{task_id}.py"
        file_path = os.path.join(tmpdir, file_name)
        
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(manim_code)
        
        # Extract scene name from code
        scene_name = extract_scene_name_from_code(manim_code)
        logger.info(f"Using scene name: {scene_name}")
        
        # Set up output directory
        output_dir = os.path.join(tmpdir, "media")
        os.makedirs(output_dir, exist_ok=True)
        
        # Run Manim command
        cmd = [
            "manim",
            "-pql",  # Preview, Quality Low (for faster rendering)
            "--output_file", f"{task_id}",  # Custom output filename
            file_path,
            scene_name
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Execute with proper error capture
        result = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True,
            text=True,
            cwd=tmpdir
        )
        
        logger.info(f"Manim stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"Manim stderr: {result.stderr}")
        
        # Find the generated video file
        # Manim typically saves to media/videos/{filename}/{quality}/{scene_name}.mp4
        possible_paths = [
            os.path.join(tmpdir, "media", "videos", task_id, "480p15", f"{scene_name}.mp4"),
            os.path.join(tmpdir, "media", "videos", task_id, "480p15", f"{task_id}.mp4"),
            os.path.join(tmpdir, f"{task_id}.mp4"),
            os.path.join(tmpdir, f"{scene_name}.mp4"),
        ]
        
        video_path = None
        for path in possible_paths:
            if os.path.exists(path):
                video_path = path
                logger.info(f"Found video at: {path}")
                break
        
        if not video_path:
            # List all files in the directory for debugging
            logger.error("Video file not found. Directory contents:")
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    logger.error(f"  {os.path.join(root, file)}")
            raise FileNotFoundError(f"Rendered video not found. Expected at one of: {possible_paths}")
        
        # Copy video to a temporary location that won't be deleted
        import shutil
        temp_video_path = f"/tmp/{task_id}.mp4"
        shutil.copy2(video_path, temp_video_path)
        return temp_video_path


# def upload_video_to_supabase(video_path: str, task_id: str, supabase: Client) -> str:
    """
    Upload video file to Supabase storage and return public URL.
    """
    try:
        with open(video_path, "rb") as file:
            file_data = file.read()

        # Upload to Supabase storage (no FileOptions needed)
        result = supabase.storage.from_("videosbucket").upload(
            path=f"{task_id}.mp4",
            file=file_data,
            file_options={"cache-control": "3600", "upsert": "false"}
        )

        if not result:
            logger.error(f"Upload error: {result.error.message}")
            raise Exception(f"Upload failed: {result.error.message}")

        logger.info(f"Upload successful for task: {task_id}")

        # Get public URL
        public_url_response = supabase.storage.from_("videosbucket").get_public_url(f"{task_id}.mp4")
        public_url = getattr(public_url_response, "public_url", None)

        if not public_url:
            raise Exception("Failed to retrieve public URL after upload.")

        # Clean up temporary file
        try:
            os.remove(video_path)
        except Exception as cleanup_error:
            logger.warning(f"Could not remove temporary file: {cleanup_error}")

        return public_url

    except Exception as e:
        logger.error(f"Error uploading to Supabase: {str(e)}")
        raise Exception(f"Failed to upload video to storage: {str(e)}")


def upload_video_to_supabase(video_path: str, task_id: str, supabase: Client) -> str:
    """
    Uploads a video file to Supabase storage and correctly returns the public URL.
    """
    try:
        # The bucket name should likely be a constant or config variable
        bucket_name = "videosbucket"
        file_path_in_bucket = f"{task_id}.mp4"

        with open(video_path, "rb") as file:
            # Note: For large files, consider a streaming upload if the library supports it.
            supabase.storage.from_(bucket_name).upload(
                path=file_path_in_bucket,
                file=file,
                # Using file object directly is often more memory-efficient
                file_options={"cache-control": "3600", "upsert": "true"} # 'upsert' is often better than 'false'
            )

        logger.info(f"Upload successful for task: {task_id}")

        # --- THIS IS THE FIX ---
        # The get_public_url method returns the string directly.
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_path_in_bucket)

        if not public_url:
            # This check is still good practice in case the SDK returns None on an error
            raise Exception("Supabase SDK returned an empty public URL.")

        return public_url

    except Exception as e:
        logger.error(f"Error during Supabase operation for task {task_id}: {str(e)}")
        # Re-raise a more specific error to be handled by the main loop
        raise Exception(f"Failed during Supabase storage operation: {str(e)}")
    finally:
        # Cleanup should happen regardless of success or failure
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Cleaned up temporary file: {video_path}")
        except Exception as cleanup_error:
            logger.warning(f"Could not remove temporary file {video_path}: {cleanup_error}")



def get_video_info(task_id: str, supabase: Client) -> dict:
    """
    Get detailed information about a video rendering task
    """
    try:
        result = supabase.table("videos") \
            .select("*") \
            .eq("task_id", task_id) \
            .maybe_single() \
            .execute()

        if result and result.data:
            return result.data
        else:
            return {"status": "not_found", "message": "Task not found"}

    except Exception as e:
        logger.error(f"Error fetching video info for task {task_id}: {str(e)}")
        return {"status": "error", "message": f"Failed to get video info: {str(e)}"}
