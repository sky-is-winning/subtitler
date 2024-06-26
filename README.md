# Automatic YouTube Subtitler

A python script to automatically generate subtitles for an uploaded YouTube video using OpenAI's Whisper API.

These subtitles should be siginficantly easier to read (as it should have correct punctuation and grammar) and also slightly more accurate than YouTube's autogenerated subtitles.

Pull requests and suggestions welcome!

## Prerequisties
Python 3 (Tested with Python 3.11.4 but other versions should work)

## Before first run

- Create an OpenAPI account, and add credit at https://platform.openai.com/settings/organization/billing/overview (The API costs around 40 US cents per hour of subtitling)
- Get an OpenAI API Key from https://platform.openai.com/api-keys
- Copy the `config.example.txt` file to `config.txt` and add your API key

- Get a YouTube client secret by:
- Going to https://console.cloud.google.com/welcome?authuser=1
- Click 'Create or select a project'
- Click 'New Project'
- Give it a name. This should be something you can easily link back to this if you forget, like 'Automatic Subtitler'
- Click on the project. Go to APIs and services -> Enabled APIs and services
- Now click 'Enabled APIs and Services'
- Search for 'YouTube Data API v3', select it, and click 'Enable'
- Now click the blue 'Create Credentials' button
- Under 'What data will you be accessing?' select 'User data'
- Fill in the App information. Again, call it something memorable like 'Automatic Subtitler', and enter the required emails. These can be any emails, they don't have to be the one associated with your email account.
- Under 'Scopes', select 'Add or Remove Scopes'
- In 'Manually add scopes', enter 'https://www.googleapis.com/auth/youtube.upload'.
- Click 'Add to table', then 'Update'
- Then save and continue.
- In 'OAuth Client ID', set the 'Application type' to 'Web application', then in in Authorised redirect URIs, click 'Add URI' and enter 'http://localhost:53467'
- Now click create, and download your credentials
- Rename the downloaded JSON file to `credentials.json` and place in the same folder as `subtitler.py`

- Run `pip install -r requirements.txt`

## How to use
- Ensure your video is either public or unlisted
- Run `python subtitler.py`
- Enter the video ID or URL when prompted
- When the app asks for permission to access your account, select the YouTube account and channel with the video on. This saves to `token.json` locally, so nobody else can access your account (unless you give them the token, so don't!)
- That's it! Your subtitles will be automatically generated and uploaded, and should start being shown to users straight away.