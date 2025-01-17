from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import requests
import json
import os
from app.core.settings import settings
import re
os.environ["GOOGLE_API_KEY"] = "AIzaSyCr5whd4_46jBsXqippmtf6Jh5eqXjN4uY"
os.environ["TAVILY_API_KEY"] = "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"
def generate_seo_content(topic, sub_keywords, target_audience, tone):
    prompt_template = (
        "Write an SEO-optimized article about '{topic}'. Include the following sub-keywords: {sub_keywords}. "
        "The article should be tailored for {target_audience} and written in a {tone} tone. "
        "Make sure the article has a clear structure, includes headings and subheadings, and ends with a call to action."
    )

    # Create the prompt using LangChain's PromptTemplate
    prompt = PromptTemplate(
        input_variables=["topic", "sub_keywords", "target_audience", "tone"],
        template=prompt_template
    )

    # Initialize the ChatGoogleGenerativeAI LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        api_key=settings.gemini_key,
        temperature=0.5,
        max_tokens=1024,
        timeout=30,
        max_retries=3,
    )

    # Create the chain
    chain = LLMChain(llm=llm, prompt=prompt)

    # Run the chain with user inputs
    result = chain.run({
        "topic": topic,
        "sub_keywords": ", ".join(sub_keywords),
        "target_audience": target_audience,
        "tone": tone
    })

    return result.strip()

def get_links_from_tavily_content(query):
    # Example Tavily API request (replace with actual endpoint and headers if necessary)
    url = "https://app.tavily.com/api/tavily_services"
    headers = {"Authorization": "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"}
    params = {"query": query}

    try:
        response = requests.post(url, headers=headers, params=params)
        response.raise_for_status()  # Raise HTTPError for bad status
        data = response.json()
        data["results"][0]["url"]
        return {item['keyword']: item['link'] for item in data.get('results', [])}
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return {}
    except ValueError:
        print("Invalid JSON response.")
        return {}

def integrate_links_into_content(content, links_dict):
    for keyword, link in links_dict.items():
        # Add the link only for the first occurrence of the keyword
        content = re.sub(
            fr"\b({re.escape(keyword)})\b",
            fr'\1 [source]({link})',
            content,
            count=1
        )
    return content

def save_output_seo(output, output_format, file_name):
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
    # Get related links from Tavily
    query = input("Enter the query to fetch related links from Tavily: ")
    links = get_links_from_tavily(query)

    # Integrate links into the content
    final_content = integrate_links_into_content(content, links)

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

