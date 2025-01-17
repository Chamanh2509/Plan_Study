from typing import Optional
from fastapi.responses import StreamingResponse
from app.core.settings import settings


def make_response(
    content: Optional[str] = None,
    file_path: Optional[str] = None,
) -> StreamingResponse:
    """The function creates a StreamingResponse object.

    Args:
        content (Optional[str], optional): Text content. Defaults to None.
        file_path (Optional[str], optional): File path, if response is Audio, PPT,...\
            Defaults to None.

    Raises:
        ValueError: If neither content nor file_path is provided.
        TypeError: If file_path is not a valid string.

    Returns:
        StreamingResponse: StreamingResponse object.
    """
    if file_path is None and content is not None:
        return StreamingResponse(
            content=content,
            media_type="application/octet-stream",
        )

    if file_path is not None:
        # Đảm bảo file_path là chuỗi, nếu không, chuyển thành chuỗi (nếu có thể)
        if not isinstance(file_path, str):
            file_path = str(file_path)
        file_name = file_path.split("/")[-1]
        media_url = f"{settings.media_base_url}/{file_name}"
        return StreamingResponse(
            content=media_url,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={file_name}"},
        )

    # Nếu không có cả content và file_path
    raise ValueError("Either content or file_path must be provided.")
