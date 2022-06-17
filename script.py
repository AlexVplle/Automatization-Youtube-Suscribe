import os
import csv
from urllib.parse import urlparse

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

scopes = ["https://www.googleapis.com/auth/youtube"]


def main():

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "Your_client_secret_file.json"

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()
    youtubeForRecipientAccount = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    print("Collect subscriptions from csv file : 1")
    print("Collect subscriptions from youtube account : 2")
    inputChoice = int(input("Enter your choice : "))
    if inputChoice not in [1, 2]:
        print("Invalid choice")
        return
    arrayOfURL = parseURLFromCSV(input("Enter csv file name : ")) if inputChoice == 1 else collectSubscriptionsFromAnotherAccount(
        api_service_name, api_version, credentials)
    for url in arrayOfURL:
        if verifyChannelExist(youtubeForRecipientAccount, url) and verifyNotAlreadySubscribed(youtubeForRecipientAccount, url):
            response = suscribeToChannel(youtubeForRecipientAccount, url)
            print(response['snippet']['title'])


def parseURLFromCSV(csvFile: str):
    arrayOfUrl = []
    with open(csvFile, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row:
                pathUrl = urlparse(row[0]).path
                basename = os.path.basename(pathUrl)
                arrayOfUrl.append(basename)
    del arrayOfUrl[0]
    return arrayOfUrl


def collectSubscriptionsFromAnotherAccount(api_service_name: str, api_version: str, credentials: object):
    arrayOfURL = []
    youtubeForSenderAccount = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)
    request = youtubeForSenderAccount.subscriptions().list(
        part="snippet,contentDetails",
        mine=True
    )
    response = request.execute()
    for channel in response['items']:
        arrayOfURL.append(channel['snippet']['resourceId']['channelId'])
    while response['nextPageToken']:
        request = youtubeForSenderAccount.subscriptions().list(
            part="snippet,contentDetails",
            mine=True,
            pageToken=response['nextPageToken']
        )
        response = request.execute()
        for channel in response['items']:
            arrayOfURL.append(channel['snippet']['resourceId']['channelId'])
    return arrayOfURL


def verifyChannelExist(YoutubeObject: object, channelId: str):
    request = YoutubeObject.channels().list(
        part="snippet,contentDetails,statistics",
        id=channelId
    )
    response = request.execute()
    if response['pageInfo']['totalResults'] == 0:
        return False
    return True


def verifyNotAlreadySubscribed(YoutubeObject: object, channelId: str):
    request = YoutubeObject.subscriptions().list(
        part="snippet",
        forChannelId=channelId
    )
    response = request.execute()
    if response['pageInfo']['totalResults'] == 0:
        return False
    return True


def suscribeToChannel(YoutubeObject: object, channelId: str):
    request = YoutubeObject.subscriptions().insert(
        part="snippet",
        body={
            "snippet": {
                "resourceId": {
                    "kind": "youtube#channel",
                    "channelId": channelId
                }
            }
        }
    )
    response = request.execute()
    return response


if __name__ == "__main__":
    main()
