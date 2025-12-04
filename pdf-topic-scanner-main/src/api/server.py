"""Small FastAPI server to expose the DocTree.AI pipeline as an HTTP API."""
import logging
import time
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi.requests import Request

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Set max file size to 500MB (default is 25MB)
max_file_size = 500 * 1024 * 1024  # 500MB

from src.core.pdf_parser import parse_pdf
from src.features.feature_engineer import enrich_blocks_with_features
from src.hierarchy.heading_classifier import classify_headings
from src.hierarchy.tree_builder import build_hierarchy

app = FastAPI(
    title="DocTree.AI API",
    version="0.1.0",
    description="PDF topic scanning and document hierarchy extraction",
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={"detail": "Too many requests. Please try again later."},
))

# In development allow all origins. Restrict in production via environment variable.
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Configure middleware to limit upload size
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.method == "POST":
        if "content-length" in request.headers:
            try:
                content_length = int(request.headers["content-length"])
                if content_length > max_file_size:
                    logger.warning(
                        f"Upload rejected: file size {content_length / (1024*1024):.1f}MB exceeds limit {max_file_size / (1024*1024):.0f}MB"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={"detail": f"File too large. Max size is {max_file_size / (1024*1024):.0f}MB"},
                    )
            except (ValueError, TypeError):
                logger.error("Invalid Content-Length header")
    return await call_next(request)


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    logger.info("Health check requested")
    return {"status": "ok", "version": "0.1.0"}


@app.post("/extract")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute per IP
async def extract_hierarchy(request: Request, file: UploadFile = File(...)):
    """
    Accepts a PDF upload, runs the DocTree pipeline, and returns the hierarchy JSON.
    
    Rate limited to 10 requests per minute per client IP to prevent abuse.
    """
    t0 = time.time()
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # Validate filename
    filename = file.filename or "unknown.pdf"
    if not filename.lower().endswith(".pdf"):
        logger.warning(f"[{request_id}] Invalid file type: {filename}")
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted",
        )
    
    logger.info(f"[{request_id}] Upload started: {filename}")
    
    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        try:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name
        except Exception as e:
            logger.error(f"[{request_id}] Error reading file: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Failed to read uploaded file",
            )

    try:
        logger.info(f"[{request_id}] Processing PDF: {filename}")
        blocks = parse_pdf(temp_path)
        logger.debug(f"[{request_id}] Parsed {len(blocks)} blocks")
        
        enriched = enrich_blocks_with_features(blocks)
        logger.debug(f"[{request_id}] Enriched blocks with features")
        
        classified = classify_headings(enriched)
        logger.debug(f"[{request_id}] Classified headings")

        page_numbers = [b.get("page", 1) for b in classified]
        total_pages = max(page_numbers) if page_numbers else 0

        metadata = {
            "source_file": filename,
            "total_blocks": len(classified),
            "total_pages": total_pages,
        }

        tree = build_hierarchy(classified, metadata)
        elapsed = time.time() - t0
        
        logger.info(
            f"[{request_id}] Successfully processed PDF in {elapsed:.2f}s. "
            f"Pages: {total_pages}, Blocks: {len(classified)}"
        )

        return {
            "ok": True,
            "duration_sec": round(elapsed, 2),
            "hierarchy": tree,
        }
    except Exception as e:
        elapsed = time.time() - t0
        logger.error(
            f"[{request_id}] Error processing PDF after {elapsed:.2f}s: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Error processing PDF. Please try again.",
        )
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.debug(f"[{request_id}] Cleaned up temp file")
        except Exception as e:
            logger.warning(f"[{request_id}] Failed to clean up temp file: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
