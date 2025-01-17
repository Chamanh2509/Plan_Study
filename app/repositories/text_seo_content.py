from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
import os
import re
import json
import requests
from bs4 import BeautifulSoup
from app.core.settings import settings


# Configure environment variables
os.environ["GOOGLE_API_KEY"] = "AIzaSyCr5whd4_46jBsXqippmtf6Jh5eqXjN4uY"
os.environ["TAVILY_API_KEY"] = "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"


def fetch_content_from_url(url):
    """Fetch the content from a given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        return " ".join(p.get_text() for p in paragraphs)
    except Exception as e:
        print(f"Error fetching content from {url}: {e}")
        return ""


def get_links_from_tavily(query):
    search_tool = TavilySearchResults(
        max_results=5,
        include_answer=False,
        include_raw_content=False,
        include_images=False,
    )

    try:
        raw_results = search_tool._run(query)
        if isinstance(raw_results, list) and raw_results:
            links_dict = {
                result.get('url'): result.get('content', '')
                for result in raw_results
                if 'url' in result
            }
            extracted_content = {
                url: {
                    "url": url,
                    "content": content if content else fetch_content_from_url(url)
                }
                for url, content in links_dict.items()
            }
            return extracted_content
        else:
            print(f"No valid results from Tavily for query: {query}")
            return {}
    except Exception as e:
        print(f"Error fetching links from Tavily: {e}")
        return {}

def compile_summary_with_citations(content_dict):
    """Compile a summary with citations from extracted content."""
    summary_parts = []
    for title, data in content_dict.items():
        content = data["content"][:500]  # Limit to 500 characters for the summary
        url = data["url"]
        summary_parts.append(f"{content} [Source: {url}]")
    return "\n\n".join(summary_parts)


def generate_seo_content_with_citations(topic, sub_keywords, target_audience, tone,
                                        summary):
    """Generate SEO-optimized content based on a summary with citations."""
    prompt_template = (
        "Write an SEO-optimized article about '{topic}'. Include the following sub-keywords: {sub_keywords}. "
        "The article should be tailored for {target_audience} and written in a {tone} tone. "
        "Use the following research data as your source:\n\n{summary}\n\n"
        "The article should have a clear structure, include headings and subheadings, and end with a call to action. "
        "Include citations inline for each piece of information from the sources provided."
    )


    # Create the prompt using LangChain's PromptTemplate
    prompt = PromptTemplate(
        input_variables=["topic", "sub_keywords", "target_audience", "tone", "summary"],
        template=prompt_template
    )

    # Initialize the ChatGoogleGenerativeAI LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        api_key=os.environ["GOOGLE_API_KEY"],
        temperature=0.5,
        max_tokens=1024,
        timeout=30,
        max_retries=3,
    )

    # Create the chain
    chain = LLMChain(llm=llm, prompt=prompt)

    # Run the chain with user inputs
    result = chain.invoke({
        "topic": topic,
        "sub_keywords": ", ".join(sub_keywords),
        "target_audience": target_audience,
        "tone": tone,
        "summary": summary,
    })

    return result.get("text")

def save_output(output, output_format, file_name):
    """Save the final output to a file."""

    if isinstance(output, str):
        if output_format == "markdown":
            with open(file_name, "w") as f:
                f.write(output)
        elif output_format == "html":
            html_content = f"<html><body><pre>{output}</pre></body></html>"
            with open(file_name, "w") as f:
                f.write(html_content)
        elif output_format == "json":
            json_data = {"content": output}
            with open(file_name, "w") as f:
                json.dump(json_data, f, indent=4)
        else:
            raise ValueError("Unsupported output format.")
    else:
        raise TypeError("Output must be a string.")

