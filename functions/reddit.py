"""Utilities for retrieving posts from Reddit RSS feeds."""

import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def get_reddit_posts(subreddit):
    """Retrieve the five most recent posts from a Reddit subreddit.

    Args:
        subreddit: The name of the Reddit subreddit to retrieve posts from.

    Returns:
        A list of dictionaries containing each post's title, author,
        and URL, or None if the request fails, the RSS feed cannot be
        parsed, or no posts are found.
    """
    url = f"https://www.reddit.com/r/{subreddit}/.rss"

    headers = {
        "User-Agent": "ecommerce-project/1.0"
    }

    try:
        request = Request(url, headers=headers)
        with urlopen(request, timeout=30) as response:
            root = ET.fromstring(response.read())

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

    except (HTTPError, URLError, TimeoutError, ET.ParseError):
        return None
