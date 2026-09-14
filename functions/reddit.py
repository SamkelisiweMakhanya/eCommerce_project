import requests


def get_reddit_posts(subreddit):
    url = f"https://www.reddit.com/r/{subreddit}.json?limit=5"

    headers = {
        "User-Agent": "ecommerce-project/1.0 by ecommerce-project"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        return {
            "error": "Unable to fetch Reddit posts.",
            "details": str(exc),
        }
