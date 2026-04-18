import re
import json
import time
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from litellm import completion
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

RELEVANT_KEYWORDS = [
    "contact", "about", "team", "staff", "owner", "founder", 
    "management", "bio", "info", "project", "service", "portfolio",
    "faq", "help", "careers", "job"
]

SUB_PATHS = ["/contact", "/contact-us", "/about", "/about-us", "/team", "/our-team"]

EMPTY_RESULT = {
    "owner_name": "",
    "business_name": "",
    "emails": [],
    "phones": [],
    "address": ""
}

class ExtractorService:
    def __init__(self, api_key, model_id="mistral/mistral-large-latest"):
        self.api_key = api_key
        self.model_id = model_id

    def fetch_html(self, url, timeout=12):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception:
            return None

    def html_to_text(self, html):
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "head"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)

    def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, "html.parser")
        found_urls = set()
        base_domain = urlparse(base_url).netloc

        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True).lower()
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)

            if parsed_url.netloc == base_domain and parsed_url.path and parsed_url.path != "/":
                match = any(kw in text or kw in parsed_url.path.lower() for kw in RELEVANT_KEYWORDS)
                if match:
                    clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                    found_urls.add(clean_url)

        return list(found_urls)

    def collect_page_text(self, base_url, status_callback=None):
        if not base_url.startswith("http"):
            base_url = "https://" + base_url

        pages_fetched = []
        visited_urls = set()
        all_text = ""

        if status_callback: status_callback(f"Fetching: {base_url}")
        html = self.fetch_html(base_url)
        if not html:
            fallback = base_url.replace("https://", "http://")
            html = self.fetch_html(fallback)

        if not html:
            return "", []

        homepage_text = self.html_to_text(html)
        all_text += homepage_text + "\n\n"
        pages_fetched.append(base_url)
        visited_urls.add(base_url)

        discovered_urls = self.extract_links(html, base_url)
        if not discovered_urls:
            for path in SUB_PATHS:
                discovered_urls.append(urljoin(base_url, path))

        fetch_count = 0
        for url in discovered_urls:
            if url in visited_urls or fetch_count >= 3:
                continue
            
            if status_callback: status_callback(f"Analyzing: {url}")
            sub_html = self.fetch_html(url)
            if sub_html:
                text = self.html_to_text(sub_html)
                if len(text) > 100:
                    all_text += f"{'='*20}\nURL: {url}\n{'='*20}\n{text}\n\n"
                    pages_fetched.append(url)
                    visited_urls.add(url)
                    fetch_count += 1
            time.sleep(0.3)

        return all_text.strip(), pages_fetched

    def regex_fallback(self, text):
        emails = list(dict.fromkeys(re.findall(r"[\w.+\-]+@[\w\-]+(?:\.\w+)+", text)))
        emails = [e for e in emails if not re.search(r"\.(png|jpg|jpeg|gif|svg|css|js)$", e, re.I)]
        phones = list(dict.fromkeys(re.findall(r"(?:\+?\d[\d\s\-().]{7,}\d)", text)))
        phones = [p.strip() for p in phones if 7 <= len(re.sub(r"\D", "", p)) <= 15]
        return emails[:5], phones[:5]

    def extract_with_ai(self, url, text):
        prompt = f"""You are a precise web data extractor. Analyze the website content below from "{url}" and extract contact/owner information.

Return ONLY a valid JSON object with these exact keys:
{{
  "owner_name": "Full name of the owner, founder, CEO, or director. Empty string if not found.",
  "business_name": "Name of the business or organization.",
  "emails": ["list", "of", "email", "addresses"],
  "phones": ["list", "of", "phone", "numbers"],
  "address": "Full physical address if found, otherwise empty string.",
}}

Website content:
{text[:12000]}"""

        try:
            # Detect if it's a Google Gemini model
            if self.model_id.startswith("gemini"):
                if not genai:
                    raise ImportError("google-genai package not found. Run 'pip install google-genai'")
                
                # Strip prefix if present
                model_name = self.model_id.split("/")[-1]
                
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                return json.loads(response.text)
            
            # Use LiteLLM for Mistral and other providers
            response = completion(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                api_key=self.api_key,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"AI Extraction Error ({self.model_id}): {e}")
            return None

    def process_url_yield(self, url, index, total):
        yield {"type": "progress", "index": index, "total": total, "url": url, "status": f"Initializing {self.model_id}..."}
        
        result = dict(EMPTY_RESULT)
        result["url"] = url

        text, pages = self.collect_page_text(url)
        
        yield {"type": "progress", "index": index, "total": total, "url": url, "status": f"Fetched {len(pages)} pages. Running AI..."}

        if not text:
            result["error"] = "Could not fetch any page"
            yield {"type": "result", "index": index, "total": total, "data": result}
            return

        data = self.extract_with_ai(url, text)

        if data:
            result.update(data)
            yield {"type": "progress", "index": index, "total": total, "url": url, "status": "AI extraction successful!"}
        else:
            emails, phones = self.regex_fallback(text)
            result["emails"] = emails
            result["phones"] = phones
            result["error"] = "AI failed — used fallback"
            yield {"type": "progress", "index": index, "total": total, "url": url, "status": "AI failed, used fallback."}

        yield {"type": "result", "index": index, "total": total, "data": result}
