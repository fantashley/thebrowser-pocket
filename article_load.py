from bs4 import BeautifulSoup
from GmailFetcher import GmailFetcher
from pathlib import Path
import os.path
import requests
import sys
import time

BROWSER_EMAIL = "robert@thebrowser.com"
PLACEHOLDER_FILE = "/data/load_complete"


def build_payload(email_content, action, tags=None):
    soup = BeautifulSoup(email_content, 'html.parser')
    pocket_payload = []
    articles = soup.find_all('h3')
    if len(articles) != 5:
        return []
    for link in articles:
        article_title = link.a.getText()
        redirect_url = link.a.get('href')
        headers = requests.utils.default_headers()
        headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        r = requests.get(redirect_url, headers=headers)
        article_url = r.url
        pocket_action = {"action": action}
        pocket_action["title"] = article_title
        pocket_action["url"] = article_url
        if tags is not None:
            pocket_action["tags"] = tags
        pocket_payload.append(pocket_action)
    return pocket_payload


fetcher = GmailFetcher()
fetcher.connect()

if os.path.exists(PLACEHOLDER_FILE):
    last_load_time = int(os.path.getmtime(PLACEHOLDER_FILE))
    browser_messages = fetcher.query_messages('me', \
            "from:({0}) after:{1}".format(BROWSER_EMAIL, last_load_time))
else:
    browser_messages = fetcher.query_messages('me', "from:({0})".format(BROWSER_EMAIL))

email_payload = []

for email in browser_messages:
    email_content = fetcher.get_message_html('me', email['id'])
    email_payload.extend(build_payload(email_content, "add", "thebrowser"))

pocket_request_data = {}
pocket_request_data['consumer_key'] = sys.argv[1]
pocket_request_data['access_token'] = sys.argv[2]
pocket_request_data['actions'] = email_payload
add_request = requests.post("https://getpocket.com/v3/send", json=pocket_request_data)
if add_request.status_code == requests.codes.ok:
    Path(PLACEHOLDER_FILE).touch()
else:
    print(add_request.text)
