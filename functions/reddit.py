import xml.etree.ElementTree as ET

import requests


def get_reddit_posts(subreddit):
    url = f"https://www.reddit.com/r/{subreddit}/.rss"

    headers = {
        "User-Agent": "ecommerce-project/1.0"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        root = ET.fromstring(response.text)

        posts = []

        for entry in root.findall(
            "{http://www.w3.org/2005/Atom}entry"
        )[:5]:
            title = entry.find(
                "{http://www.w3.org/2005/Atom}title"
            )
            author = entry.find(
                "{http://www.w3.org/2005/Atom}author/"
                "{http://www.w3.org/2005/Atom}name"
            )
            link = entry.find(
                "{http://www.w3.org/2005/Atom}link"
            )

            posts.append({
                "title": title.text if title is not None else "",
                "author": author.text if author is not None else "",
                "url": link.attrib["href"] if link is not None else "",
            })

        if not posts:
            return None
        return posts

    except (requests.RequestException, ET.ParseError):
        return None
