import requests
from bs4 import BeautifulSoup


def extract_article(url):
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        paragraphs = soup.find_all("p")

        content = " ".join(
            paragraph.get_text(" ", strip=True)
            for paragraph in paragraphs
        )

        return content

    except Exception as e:
        print(f"Error extracting article: {e}")
        return ""


if __name__ == "__main__":
    test_url = "https://example.com"

    article = extract_article(test_url)

    print("\nExtracted Article:\n")
    print(article[:2000])