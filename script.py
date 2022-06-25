import os
import csv
from urllib.parse import urlparse

import google_auth_oauthlib.flow
import googleapiclient.discovery

scopes = ["https://www.googleapis.com/auth/youtube"] # API authorization


def main():
    """
    Main function
    """

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # Allows to use insecure transport for the script to work

    api_service_name = "youtube" # API service name
    api_version = "v3" # API version
    client_secrets_file = "your_secret_client_file.json" # Client secrets file

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes) # Creates a flow object to get the authorizations
    credentials = flow.run_console() # Runs the flow to get the authorizations
    youtubeForRecipientAccount = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials) # Creates a Youtube object to use the API

    # Prompts the user to choose the way to collect the subscriptions
    print("Collect subscriptions from csv file : 1")
    print("Collect subscriptions from youtube account : 2")
    print("Write channel name : 3")
    inputChoice = int(input("Enter your choice : "))

    if inputChoice not in [1, 2, 3]: # Checks if the input is valid
        print("Invalid choice")
        return

    # If the user wants to collect the subscriptions from a csv file
    if inputChoice == 1:
        arrayOfURL = parseChannelIdFromCSV(input("Enter csv file name : ")) # Gets the channel ids from the csv file

    # If the user wants to collect the subscriptions from a youtube account
    elif inputChoice == 2: 
        arrayOfURL = collectSubscriptionsFromAccount(
            api_service_name, api_version, flow)

    # If the user wants to collect the subscriptions from keyboard
    else: 
        arrayOfURL = []
        channelName = input("Enter channel name or enter 'q' : ")
        while channelName != 'q':
            arrayOfURL.append(retrieveChannelIdFromChannelName(
                youtubeForRecipientAccount, channelName)) # Gets the channel id from the channel name

    for url in arrayOfURL: # For each channel id
        if verifyChannelExist(youtubeForRecipientAccount, url) and verifyNotAlreadySubscribed(youtubeForRecipientAccount, url): # Checks if the channel exists and if the user is not already subscribed
            response = suscribeToChannel(youtubeForRecipientAccount, url) # Subscribes the user to the channel
            print(response['snippet']['title']) # Prints the channel name


def parseChannelIdFromCSV(csvFile: str):
    """
    Parses the channel ids from the csv file
    @param csvFile: The csv file name
    @return arrayOfURL: The array of channel ids
    """

    arrayOfUrl = []
    with open(csvFile, 'r') as csvfile: # Opens the csv file
        reader = csv.reader(csvfile) # Creates a reader object
        for row in reader: # For each row in the csv file
            if row: # If the row is not empty
                pathUrl = urlparse(row[0]).path # Gets the path from the url
                basename = os.path.basename(pathUrl) # Gets the channel ID from the path
                arrayOfUrl.append(basename) # Adds the channel ID to the array
    del arrayOfUrl[0] # Deletes the titles of the array
    return arrayOfUrl # Returns the array of channel IDs


def collectSubscriptionsFromAccount(api_service_name: str, api_version: str, flow: object):
    """
    Collects the subscriptions from a youtube account
    @param api_service_name: The API service name
    @param api_version: The API version
    @param flow: The flow object
    @return arrayOfURL: The array of channel ids
    """

    arrayOfURL = []
    credentials = flow.run_console() # Runs the flow to get the authorizations for sender account
    youtubeForSenderAccount = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials) # Creates a Youtube object to use the API
    request = youtubeForSenderAccount.subscriptions().list(
        part="snippet,contentDetails",
        mine=True
    ) 
    response = request.execute() # send request to API
    for channel in response['items']: # For each channel in the response
        arrayOfURL.append(channel['snippet']['resourceId']['channelId']) # Adds the channel ID to the array
    while hasattr(response, 'nextPageToken'): # While there is a next page
        request = youtubeForSenderAccount.subscriptions().list(
            part="snippet,contentDetails",
            mine=True,
            pageToken=response['nextPageToken']
        )
        response = request.execute() # send request to API
        for channel in response['items']: # For each channel in the response
            arrayOfURL.append(channel['snippet']['resourceId']['channelId']) # Adds the channel ID to the array
    return arrayOfURL # Returns the array of channel IDs


def verifyChannelExist(YoutubeObject: object, channelId: str):
    """
    Verifies if the channel exists
    @param YoutubeObject: The Youtube object
    @param channelId: The channel ID
    @return: True if the channel exists, False otherwise
    """

    request = YoutubeObject.channels().list(
        part="snippet,contentDetails,statistics",
        id=channelId
    )
    response = request.execute() # send request to API
    if response['pageInfo']['totalResults'] == 0: # If the channel doesn't exist
        return False 
    return True


def verifyNotAlreadySubscribed(YoutubeObject: object, channelId: str):
    """
    Verifies if the user is not already subscribed to the channel
    @param YoutubeObject: The Youtube object
    @param channelId: The channel ID
    @return: True if the user is not already subscribed, False otherwise
    """

    request = YoutubeObject.subscriptions().list(
        part="snippet",
        mine=True,
        forChannelId=channelId
    )
    response = request.execute() # send request to API
    if response['pageInfo']['totalResults'] == 0: # If the user is not already subscribed
        return True
    return False


def suscribeToChannel(YoutubeObject: object, channelId: str):
    """
    Subscribes the user to the channel
    @param YoutubeObject: The Youtube object
    @param channelId: The channel ID
    @return: The response from the API
    """

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
    response = request.execute() # send request to API
    return response


def removeSubscription(YoutubeObject: object, channelId: str):
    """
    Removes the subscription of the user to the channel
    @param YoutubeObject: The Youtube object
    @param channelId: The channel ID
    @return response: The response of the API
    """

    request = YoutubeObject.subscriptions().delete(
        id=channelId
    )
    response = request.execute() # send request to API
    return response


def retrieveChannelIdFromChannelName(YoutubeObject: object, channelName: str):
    """
    Retrieves the channel ID from the channel name
    @param YoutubeObject: The Youtube object
    @param channelName: The channel name
    @return channelId: The channel ID
    """

    request = YoutubeObject.channels().list(
        part="snippet",
        forUsername=channelName
    )
    response = request.execute() # send request to API
    return response['items'][0]['id'] # Returns the channel ID


if __name__ == "__main__": # Launches the main function
    main()
