"""
Cloudinary Service for P2P Palestine
Handles image uploads for Proof of Funds and KYC verification.
"""
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from app.core.config import get_settings

settings = get_settings()

# Configure Cloudinary from environment variables
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


async def upload_proof_of_funds(file: UploadFile, user_id: int) -> str:
    """
    Upload a proof of funds image to Cloudinary.
    
    Args:
        file: The uploaded file from FastAPI
        user_id: The ID of the user uploading (for folder organization)
    
    Returns:
        The secure URL of the uploaded image
    
    Raises:
        HTTPException: If upload fails
    """
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Upload to Cloudinary in p2p_proofs folder
        result = cloudinary.uploader.upload(
            file_content,
            folder="p2p_proofs",
            public_id=f"user_{user_id}_proof_{file.filename}",
            resource_type="image"
        )
        
        return result["secure_url"]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image: {str(e)}"
        )


async def upload_kyc_document(file: UploadFile, user_id: int, doc_type: str) -> str:
    """
    Upload a KYC document to Cloudinary.
    
    Args:
        file: The uploaded file from FastAPI
        user_id: The ID of the user uploading
        doc_type: Type of document (e.g., "passport", "id_card", "bank_statement")
    
    Returns:
        The secure URL of the uploaded document
    """
    try:
        file_content = await file.read()
        
        result = cloudinary.uploader.upload(
            file_content,
            folder="p2p_kyc",
            public_id=f"user_{user_id}_{doc_type}_{file.filename}",
            resource_type="image"
        )
        
        return result["secure_url"]
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload KYC document: {str(e)}"
        )
