from fastapi.responses import StreamingResponse
from fastapi.routing import APIRouter
from app.repositories.lesson_plan import generate_plan, load_grade_content, save_output_lesson_plan
from app.schemas.request_schema import GenerateTextRequest
from app.utils.api_utils import make_response
from app.web.api import echo, monitoring
from app.repositories.content_seo_text import generate_seo_content, get_links_from_tavily_content, integrate_links_into_content, save_output_seo
from app.repositories.text_seo_content import generate_seo_content_with_citations, get_links_from_tavily, compile_summary_with_citations, fetch_content_from_url, save_output
from app.repositories.rubric_generator import save_result, create_student_evaluation
from fastapi import HTTPException, Form
from app.core.settings import settings
import requests
import json
from app.repositories.model import SEORequest
import traceback
import logging
import os


api_router = APIRouter()
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(echo.router, prefix="/echo", tags=["echo"])

logger = logging.getLogger(__name__)
@api_router.post("/generate_text")
async def generate_text(request: GenerateTextRequest) -> StreamingResponse:
    """Test generator text response."""
    text = request.input_text
    generated_text = generate_text(text)
    return make_response(content=generated_text)
@api_router.post("/generate_study_plan")
async def generate_study_plan(grade: str, topic: str, output_format: str = "markdown") -> StreamingResponse:
    """
    Generate study plan and learning objectives and save in the specified format..
    """
    try:
        # Load grade content from an external file
        grade_content = load_grade_content("app/grade_content.json")

        # Generate plan and objectives
        generated_plan = generate_plan(grade, topic, grade_content)

        # Validate output format
        if output_format not in ["markdown", "html", "json"]:
            return make_response(
                {"error": f"Unsupported output format: {output_format}"}, 400)

        # Save the generated plan to a file in the specified format
        file_name = f"study_plan.{output_format}"
        save_output(generated_plan, output_format, file_name)

        # Return the file as a StreamingResponse
        file = open(file_name, "r")
        media_type = (
            "text/markdown" if output_format == "markdown"
            else "text/html" if output_format == "html"
            else "application/json"
        )
        return StreamingResponse(file, media_type=media_type)

    except Exception as e:
        import traceback
        print("Error:", traceback.format_exc())
        return make_response({"error": str(e)}, 400)

@api_router.post("/generate_seo")
async def generate_seo(topic: str, sub_keywords: str, target_audience: str, tone: str, query: str):
    """
    Generate SEO content with integrated links from Tavily.
    """
    try:
        # Generate SEO content
        sub_keywords_list = sub_keywords.split(',')
        content = generate_seo_content(topic, sub_keywords_list, target_audience, tone)

        # Fetch related links from Tavily
        links = get_links_from_tavily(query)

        # Integrate links into the SEO content
        final_content = integrate_links_into_content(content, links)

        # Save the final content to a file
        output_file = "generated_seo_content.txt"
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(final_content)

        # Return the file as a streaming response
        file = open(output_file, "r", encoding="utf-8")
        return StreamingResponse(file, media_type="text/plain")

    except Exception as e:
        import traceback
        print("Error:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))



@api_router.post("/text_seo_content")
async def text_seo_content(topic: str, sub_keywords: str, target_audience: str, tone: str, output_format: str):
    try:
        # Step 1: Validate output format
        valid_formats = ["markdown", "html", "json"]
        if output_format not in valid_formats:
            raise HTTPException(status_code=400, detail=f"Unsupported output format: {output_format}")

        # Step 2: Search for links using Tavily
        content_dict = get_links_from_tavily(topic)
        if not content_dict:
            raise HTTPException(status_code=404, detail="No content found for the given topic.")

        # Step 3: Compile a summary with citations
        summary = compile_summary_with_citations(content_dict)

        # Step 4: Generate SEO content
        seo_content = generate_seo_content_with_citations(topic, sub_keywords, target_audience, tone, summary)

        # Step 5: Save the generated content to a file
        file_name = f"{topic.replace(' ', '_')}_seo_content.{output_format}"
        output_path = os.path.join(settings.media_dir_static, file_name)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write the content to the file
        with open(output_path, "w") as f:
            f.write(seo_content if isinstance(seo_content, str) else seo_content["text"])  # Handle dict or string output

        # Step 6: Return the file as a streaming response
        media_type = {
            "markdown": "text/markdown",
            "html": "text/html",
            "json": "application/json",
        }.get(output_format, "text/plain")

        return StreamingResponse(open(output_path, "rb"), media_type=media_type)

    except HTTPException as http_exc:
        raise http_exc  # Reraise known HTTP exceptions
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@api_router.post("/generate_rubric")
async def generate_rubric(grade: str, topic: str, point_scale, language: str, output_format: str = "markdown") -> StreamingResponse:
    try:
        # Generate the evaluation content
        generated_rubric = create_student_evaluation(grade, topic, point_scale, language)

        # Validate output format
        if output_format not in ["markdown", "html", "json"]:
            return make_response({"error": f"Unsupported output format: {output_format}"}, 400)

        # Save the generated rubric to a file in the specified format
        file_name = f"rubric.{output_format}"
        save_output(generated_rubric, output_format, file_name)

        # Return the file as a StreamingResponse
        file = open(file_name, "r", encoding="utf-8")
        media_type = (
            "text/markdown" if output_format == "markdown"
            else "text/html" if output_format == "html"
            else "application/json"
        )
        return StreamingResponse(file, media_type=media_type)

    except Exception as e:
        import traceback
        print("Error:", traceback.format_exc())
        return make_response({"error": str(e)}, 400)



