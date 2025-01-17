from pydantic import BaseModel

class SEORequest(BaseModel):
    topic: str
    sub_keywords: list
    target_audience: str
    tone: str
    output_format: str = "html"
    output_file: str = "seo_content.html"
