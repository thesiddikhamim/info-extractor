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

PRIORITY_KEYWORDS = {
    "contact": 10,
    "about": 10,
    "team": 3,
    "staff": 3,
    "owner": 3,
    "founder": 3,
    "leadership": 3,
    "management": 2,
    "bio": 2,
    "who": 2,
    "info": 1,
    "profile": 1,
    "location": 1
}

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
        title = soup.title.string if soup.title else ""
        clean_title = title.strip() if title else ""

        for tag in soup(["script", "style", "nav", "footer", "head", "header", "aside", "iframe", "svg", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text, clean_title

    def extract_links(self, html, base_url):
        soup = BeautifulSoup(html, "html.parser")
        found_urls = {} # url -> max_score
        base_domain = urlparse(base_url).netloc

        for a in soup.find_all("a", href=True):
            href = a["href"].split("#")[0].rstrip("/")
            if not href: continue
            
            text = a.get_text(separator=" ", strip=True).lower()
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)

            if parsed_url.netloc == base_domain and parsed_url.path and parsed_url.path != "/":
                path_lower = parsed_url.path.lower()
                # Normalize text and path for better matching (e.g., "about-us" -> "about us")
                normalized_text = text.replace("-", " ").replace("_", " ")
                normalized_path = path_lower.replace("-", " ").replace("_", " ")
                
                max_score = 0
                for kw, score in PRIORITY_KEYWORDS.items():
                    # Strict matching: keyword must be at the start of a word
                    # This prevents matching "information" for "info" unless it starts with it
                    pattern = rf"\b{re.escape(kw)}"
                    
                    if re.search(pattern, normalized_text) or re.search(pattern, normalized_path):
                        # Base score is the keyword score
                        match_score = score
                        
                        # High bonus for exactly starting with the keyword (prefix)
                        is_prefix = (
                            normalized_text.startswith(kw) or 
                            normalized_path.startswith(f"/{kw}") or 
                            normalized_path.startswith(kw)
                        )
                        
                        if is_prefix:
                            match_score += 5
                        
                        max_score = max(max_score, match_score)
                
                if max_score > 0:
                    clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path.rstrip('/')}"
                    if clean_url not in found_urls or max_score > found_urls[clean_url]:
                        found_urls[clean_url] = max_score

        # Return list of (URL, Score) tuples, sorted by score descending
        return sorted(found_urls.items(), key=lambda x: x[1], reverse=True)

    def collect_page_text(self, base_url):
        if not base_url.startswith("http"):
            base_url = "https://" + base_url

        pages_fetched = []
        visited_urls = set()
        all_text = ""

        yield {"status": "fetching", "url": base_url}
        html = self.fetch_html(base_url)
        if not html:
            fallback = base_url.replace("https://", "http://")
            yield {"status": "fetching_fallback", "url": fallback}
            html = self.fetch_html(fallback)

        if not html:
            yield {"status": "error", "msg": "Could not fetch homepage"}
            return "", []

        homepage_text, title = self.html_to_text(html)
        yield {"status": "fetched", "url": base_url, "title": title}
        
        all_text += homepage_text + "\n\n"
        pages_fetched.append({"url": base_url, "title": title})
        visited_urls.add(base_url)

        discovered_links = self.extract_links(html, base_url)
        # Note: Fallback SUB_PATHS removed as per user request to only fetch explicitly found matched pages.

        fetch_count = 0
        limit = 8 # Increased limit
        
        for url, score in discovered_links:
            # Skip if visited, or if we hit the limit (unless it's a very high priority page)
            if url in visited_urls:
                continue
            
            if fetch_count >= limit and score < 4:
                continue
            
            yield {"status": "analyzing", "url": url}
            sub_html = self.fetch_html(url)
            if sub_html:
                text, sub_title = self.html_to_text(sub_html)
                if len(text) > 100:
                    yield {"status": "fetched", "url": url, "title": sub_title}
                    all_text += f"{'='*20}\nURL: {url}\n{'='*20}\n{text}\n\n"
                    pages_fetched.append({"url": url, "title": sub_title})
                    visited_urls.add(url)
                    fetch_count += 1
            time.sleep(0.3)

        yield {"status": "complete", "all_text": all_text.strip(), "pages": pages_fetched}

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
{text[:100000]}"""

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

        text = ""
        pages = []
        
        for event in self.collect_page_text(url):
            if event["status"] == "fetching":
                yield {"type": "progress", "index": index, "total": total, "url": url, "status": f"Fetching homepage..."}
            elif event["status"] == "fetching_fallback":
                yield {"type": "progress", "index": index, "total": total, "url": url, "status": f"Retrying with HTTP..."}
            elif event["status"] == "fetched":
                title_str = f" \"{event['title']}\"" if event['title'] else ""
                yield {"type": "progress", "index": index, "total": total, "url": url, "status": f"Fetched{title_str}"}
            elif event["status"] == "analyzing":
                yield {"type": "progress", "index": index, "total": total, "url": url, "status": f"Analyzing sub-page..."}
            elif event["status"] == "complete":
                text = event["all_text"]
                pages = event["pages"]
            elif event["status"] == "error":
                yield {"type": "progress", "index": index, "total": total, "url": url, "status": f"Error: {event['msg']}"}

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
