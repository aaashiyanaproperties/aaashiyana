from fastapi import HTTPException, UploadFile

from app.core.config import settings


class UploadService:
    allowed_types = {"image/jpeg", "image/png", "image/webp"}

    def upload(self, file: UploadFile) -> dict:
        if file.content_type not in self.allowed_types:
            raise HTTPException(415, "Only JPG, PNG and WebP images are accepted")
        content = file.file.read(settings.max_upload_mb * 1024 * 1024 + 1)
        if len(content) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, "Image exceeds upload size limit")
        valid_signature = (
            file.content_type == "image/jpeg" and content.startswith(b"\xff\xd8\xff")
        ) or (
            file.content_type == "image/png"
            and content.startswith(b"\x89PNG\r\n\x1a\n")
        ) or (
            file.content_type == "image/webp"
            and content.startswith(b"RIFF")
            and content[8:12] == b"WEBP"
        )
        if not valid_signature:
            raise HTTPException(415, "Image content does not match its declared file type")
        if not all(
            [
                settings.cloudinary_cloud_name,
                settings.cloudinary_api_key,
                settings.cloudinary_api_secret,
            ]
        ):
            raise HTTPException(
                503,
                "Image storage is not configured. Configure Cloudinary credentials.",
            )
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )
        result = cloudinary.uploader.upload(
            content,
            folder="aashiyana/properties",
            resource_type="image",
        )
        return {"url": result["secure_url"], "public_id": result["public_id"]}
