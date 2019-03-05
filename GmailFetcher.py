from __future__ import print_function
import base64
import pickle
import os.path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailFetcher:

    def __init__(self):

        self.service = None

    def connect(self):

        creds = None

        if os.path.exists('/data/token.pickle'):
            with open('/data/token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    '/data/credentials.json', SCOPES)
                creds = flow.run_local_server()

            with open('/data/token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)

    def query_messages(self, user_id, query=''):

        try:
            response = self.service.users().messages().list(userId=user_id,
                                                            q=query).execute()
            messages = []
            if 'messages' in response:
                messages.extend(response['messages'])

            while 'nextPageToken' in response:
                page_token = response['nextPageToken']
                response = self.service.users().messages().list(userId=user_id, q=query,
                                                                pageToken=page_token).execute()
                messages.extend(response['messages'])

            return messages
        except HttpError as error:
            print('An error occurred: {0}'.format(error))

    def get_message_html(self, user_id, msg_id):

        try:
            message = self.service.users().messages().get(userId=user_id, id=msg_id).execute()

            if 'parts' not in message['payload']:
                return ""
            if len(message['payload']['parts']) <= 1:
                return ""

            message_content = message['payload']['parts'][1]['body']['data']
            return base64.urlsafe_b64decode(message_content)
        except HttpError as error:
            print('An error occurred: {0}'.format(error))
