import json
import os
import requests
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.settings import settings

os.environ["GEMINI_API_KEY"] = "AIzaSyCr5whd4_46jBsXqippmtf6Jh5eqXjN4uY"

def create_student_evaluation(grade, topic, point_scale, language):
    try:
        llm = ChatGoogleGenerativeAI (
            model="gemini-1.5-pro",
            api_key=settings.gemini_key,
            temperature=0.5,
            max_tokens=1024,
            timeout=30,
            max_retries=3,
        )
        evaluation_prompt = PromptTemplate  (
            input_variables=["grade", "topic", "point_scale", "language"],
            template=(
                "Generate evaluation criteria for grade {grade} on the topic '{topic}' in {language} using a {point_scale}-point scale. "
                "Base the criteria on Bloom's Taxonomy and include:"
                "1. Knowledge: Define what students should recall or recognize."
                "2. Comprehension: Define how students should demonstrate understanding."
                "3. Application: Define tasks where students apply knowledge. "
                "4. Analysis: Define how students analyze or break down information."
                "5. Synthesis: Define how students combine ideas to create something new."
                "6. Evaluation: Define how students critically evaluate or make judgments."
            )
        )
        chain = evaluation_prompt | llm
        response = chain.invoke({"grade": grade, "topic": topic, "point_scale": point_scale, "language":language})

        if hasattr(response, "content"):
            return response.content
        else:
            return str(response)
    except Exception as e:
        raise RuntimeError(f"Error generating evaluation framework: {str(e)}")

def save_result(output, output_format, file_name):
    """
    Saves the generated evaluation in the desired format.
    """
    if isinstance(output, str):  # Validate output is a string
        if output_format == "markdown":
            with open(file_name, "w") as f:
                f.write(output)
        elif output_format == "html":
            html_content = f"<html><body><pre>{output}</pre></body></html>"
            with open(file_name, "w") as f:
                f.write(html_content)
        elif output_format == "json":
            evaluation_json = {"evaluation": output.split("\n")}
            with open(file_name, "w") as f:
                json.dump(evaluation_json, f, indent=4)
        else:
            raise ValueError("Unsupported output format.")
    else:
        raise TypeError("Output must be a string.")

def main():
    # Giả sử các biến này được định nghĩa trước
    generated_questions = "Sample questions for the quiz"
    output_format = "html"  # Có thể là 'markdown', 'html', hoặc 'json'
    settings = type("Settings", (object,), {"media_dir_static": "/var/www/media/"})()

    # Tạo tên file và đường dẫn
    output_file = f"rubric.{output_format}"
    output_path = os.path.join(settings.media_dir_static, output_file)

    # Lưu dữ liệu
    save_result(generated_questions, output_format, output_path)
    print(f"File saved at: {output_path}")

# Hàm giả định format_questions_to_json (nếu cần)
def format_questions_to_json(output):
    # Chuyển đổi chuỗi output thành JSON mẫu
    return {"questions": output.split("\n")}
