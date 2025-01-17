import json
import os
#from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.settings import settings
# Define prompt templates
plan_prompt = PromptTemplate(
    input_variables=["grade", "topic"],
    template=(
        "Create a study plan and learning objectives for grade {grade} on the topic: {topic}.\n"
        "The output should include: \n"
        "1. A detailed teaching plan.\n"
        "2. Learning objectives for students.\n"
        "3. Key activities and methods to achieve the objectives."
    )
)
os.environ["GOOGLE_API_KEY"] = "AIzaSyCr5whd4_46jBsXqippmtf6Jh5eqXjN4uY"
def load_grade_content(file_path):
    """Loads grade content from an external JSON file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in file: {file_path}")


def generate_plan(grade, topic, grade_content):
    """Generates a teaching plan and learning objectives based on grade and topic."""
    grade = grade.lower().strip()
    topic = topic.lower().strip()

    content = grade_content.get(grade, {}).get(topic)
    print(content)
    if not content:
        raise ValueError(f"Content for grade '{grade}' and topic '{topic}' not found.")

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            api_key=settings.gemini_key,
            temperature=0.5,
            max_tokens=1024,
            timeout=30,
            max_retries=3,
        )
        plan_chain = plan_prompt | llm
        plan = plan_chain.invoke({"grade": grade, "topic": topic})
        if hasattr(plan, "content"):
            return plan.content
        else:
            return str(plan)
    except Exception as e:
        raise RuntimeError(f"Error generating plan: {str(e)}")


# Định nghĩa hàm save_output
def save_output_lesson_plan(output, output_format, file_name):
    """
    Saves the generated questions in the desired format.
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
            # Giả sử format_questions_to_json đã được định nghĩa ở đâu đó
            kahoot_json = format_questions_to_json(output)
            with open(file_name, "w") as f:
                json.dump(kahoot_json, f, indent=4)
        else:
            raise ValueError("Unsupported output format.")
    else:
        raise TypeError("Output must be a string.")

# Sử dụng hàm save_output
def main():
    # Giả sử các biến này được định nghĩa trước
    generated_questions = "Sample questions for the quiz"
    output_format = "html"  # Có thể là 'markdown', 'html', hoặc 'json'
    settings = type("Settings", (object,), {"media_dir_static": "/var/www/media/"})()

    # Tạo tên file và đường dẫn
    output_file = f"plan_study.{output_format}"
    output_path = os.path.join(settings.media_dir_static, output_file)

    # Lưu dữ liệu
    save_output(generated_questions, output_format, output_path)
    print(f"File saved at: {output_path}")

# Hàm giả định format_questions_to_json (nếu cần)
def format_questions_to_json(output):
    # Chuyển đổi chuỗi output thành JSON mẫu
    return {"questions": output.split("\n")}


