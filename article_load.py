from bs4 import BeautifulSoup
from GmailFetcher import GmailFetcher
import requests
import sys

BROWSER_EMAIL = "robert@thebrowser.com"


def build_payload(email_content, action, tags=None):
    soup = BeautifulSoup(email_content, 'html.parser')
    pocket_payload = []
    articles = soup.find_all('h3')
    if len(articles) != 5:
        return []
    for link in articles:
        article_title = link.a.getText()
        redirect_url = link.a.get('href')
        r = requests.get(redirect_url)
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
