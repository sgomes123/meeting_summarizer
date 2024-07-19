# streamlit run streamlit-hello.py

# To run the app, you need to create a virtual environment and install the required packages.
# Go to **src/streamlit_app** folder
# cd src/streamlit_app
# Install the required packages using venv:
# python3 -m venv env
# source env/bin/activate
# pip install -r requirements.txt
# Execute it using streamlit
# streamlit run streamlit-hello.py

import streamlit as st
import boto3
import time
from utils.streamlitutils import *
import json
from utils.auth import Auth
from config_file import Config


# ID of Secrets Manager containing cognito parameters
secrets_manager_id = Config.SECRETS_MANAGER_ID

# Initialise CognitoAuthenticator
authenticator = Auth.get_authenticator(secrets_manager_id)

# Authenticate user, and stop here if not logged in
is_logged_in = authenticator.login()
if not is_logged_in:
    st.stop()


def logout():
    authenticator.logout()


with st.sidebar:
    st.text(f"Welcome,\n{authenticator.get_username()}")
    st.button("Logout", "logout_btn", on_click=logout)

# Set the app title 
st.title('Peronal Meeting Summarizer Assistant') 
# Add a welcome message 
st.write('Welcome to your own meeting summarizer assistant!') 

# input form to upload a file to s3 bucket
file = st.file_uploader("""Upload a meeting recording in mp3, mp4 or m4a format from your local desktop, 
                        and the application will guide you to extract agenda, action items and meeting notes for you:""")


# check if the file format is not among mp3, mp4 or m4a, then display an error message in a popup window and stop the app
fileUploaded = False
#fileTranscribed = False
#user_input_transcription = ""
delete_files = False

if 'fileTranscribed' not in st.session_state:
    st.session_state.fileTranscribed = False

if 'user_input_transcription' not in st.session_state:
    st.session_state.user_input_transcription = ""

if 'llm_review_response' not in st.session_state:
    st.session_state.llm_review_response = ""

if 'user_input_attendees_agenda' not in st.session_state:
    st.session_state.user_input_attendees_agenda = ""

if 'user_input_meeting_notes' not in st.session_state:
    st.session_state.user_input_meeting_notes = ""

#define the variables for s3 bucket and key
bucket_name = BUCKET_NAME
key = KEY

user_input_attendees_agenda = st.text_area("Copy list of invitees and meeting subject and agenda: ", "", height=100, key="MeetingDetails")
user_input_meeting_notes = st.text_area("Put any rough meeting notes you may have captured: ", "", height=200, key="MeetingNotes")
user_input_delete_choice = st.checkbox("Do you want to delete uploaded info after notes generation?", value=True)

if user_input_delete_choice:
    delete_files = True

if st.button("Submit for Analysis"):
    if (user_input_meeting_notes == "" and file is None):
        st.info ("Please upload a meeting recording file, or your meeting notes to proceed...")
        st.stop()

    if file is not None:
        fileType = file.type.split('/')[-1]
        #print(fileType)
        if fileType not in ['mp3', 'mp4', 'm4a', 'x-m4a']:
            st.error('Invalid file format. Please upload a file in mp3, mp4 or m4a format to proceed.')
            file = None
            st.stop()

    if file is not None:
        with file:

            bucket = f'{bucket_name}'
            filename = key + conform_to_regex(file.name)
            
            s3_client = boto3.client('s3')
            #check if file already exists in the bucket
            try:
                # check if a prefix exists in a bucket
                s3_client.put_object(Bucket=bucket, Key=(key))
            except Exception as e:
                st.error(f'Error creating key in bucket: {e}')
                st.stop()

            try:
                s3_client.head_object(Bucket=bucket, Key=filename)
                fileUploaded = True
            except Exception as e:
                st.info("File does not exist in S3, uploading... "+get_current_time())

            if not fileUploaded:
                try:
                    #st.info("Filename being uploaded: " + filename)
                    s3_client.upload_fileobj(file, bucket, filename)
                    st.success("File uploaded successfully! "+get_current_time())
                    fileUploaded = True
                except Exception as e:
                    st.error(f'Error uploading file: {e}')
            else:
                fileUploaded = True

            # check if transcription file is available
            try:
                s3_client.head_object(Bucket=bucket, Key=f'{filename}.json')
                #fileTranscribed = True
                st.session_state.fileTranscribed = True
            except Exception as e:
                st.info("Transcription does not exist in S3, transcribing... "+get_current_time())

            if not st.session_state.fileTranscribed:
                try:
                    if fileUploaded:
                        date_time = get_current_datetime()
                        job_name = 'transcribe-media-' + date_time
                        try:
                            transcribe_client = boto3.client('transcribe', region_name='us-east-1')
                        except Exception as e:
                            st.error(f'Error creating Transcribe client: {e}')
                            st.stop()

                        # Start transcription job
                        transcribe_client.start_transcription_job(
                            TranscriptionJobName=job_name,
                            Media={'MediaFileUri': f's3://{bucket_name}/{filename}'},
                            MediaFormat=filename.split('.')[-1],
                            LanguageCode='en-US',
                            OutputBucketName=bucket_name,
                            OutputKey=f'{filename}.json'
                        )
                        st.info('Transcription job started. Please wait... '+get_current_time())
                        # Wait for the transcription job to complete
                        while True:
                            status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
                            if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                                break
                            print(f"Waiting for transcription job to complete. Current status: {status['TranscriptionJob']['TranscriptionJobStatus']}")
                            time.sleep(5)

                        # Check if the transcription job was successful
                        if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
                            st.info('Transcription job completed successfully! '+get_current_time())
                            output_file_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                            st.info(f'Transcription output file: {output_file_uri}')
                            st.session_state.fileTranscribed = True
                        else:
                            st.info('Transcription job failed. '+ get_current_time())
                            failure_reason = status['TranscriptionJob']['FailureReason']
                            st.info(f'Failure reason: {failure_reason}')
                            st.session_state.fileTranscribed = False
                        #delete transcribe job
                        transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)


                except Exception as e:
                    st.error(f'Error uploading file: {e}')
            else:
                st.session_state.fileTranscribed = True
            
    # capture the transcribed output to a string variable
    if st.session_state.fileTranscribed:
        s3_resource = boto3.resource('s3')
        obj = s3_resource.Object(bucket_name, f'{filename}.json')
        full_transcription = obj.get()['Body'].read().decode('utf-8')
        transcribed_text = full_transcription.split('transcripts')[1].split('}')[0].split(':[{"transcript')[1].split(':')[1]
        st.session_state.user_input_transcription = st.text_area("Transcribed text: ", transcribed_text, height=500)

    st.info("Please proceed to generate notes by hitting 'Review Meeting Notes': ")
    
# Create a Bedrock Runtime client in the AWS Region of your choice.
client = boto3.client("bedrock-runtime", region_name="us-east-1")
# Set the model ID, e.g., Claude 3 Haiku.
model_id = "anthropic.claude-3-haiku-20240307-v1:0"

user_input_prompt = st.text_area("Please modify your prompt based on your needs:", USER_PROMPT)
    
if st.button('Review Meeting Notes'):
    # Re-validate inputs
    if (user_input_meeting_notes == "" and file is None):
        st.info ("Please upload a meeting recording file, or your meeting notes to proceed...")
        st.stop()
    if (not st.session_state.fileTranscribed and user_input_meeting_notes == ""):
        st.info ("Please 'Submit Analysis' first...")
        st.stop()

    # Define the prompt for the model.
    prompt_review = SYSTEM_PROMPT_REVIEW + "\n" + TEMPLATE_FORMAT + "\n" + EXAMPLE_REVIEW + "\n" + user_input_prompt +": \n"  \
                    + user_input_attendees_agenda +"\n" + st.session_state.user_input_transcription +"\n" + user_input_meeting_notes
    
    # Format the request payload using the model's native structure.
    request_review = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 10000,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt_review}],
            }
        ],
    }

    # Convert the native request to JSON.
    request_review = json.dumps(request_review)

    try:
        # Invoke the model with the request.
        response_review = client.invoke_model(modelId = model_id, body = request_review)

    except Exception as e:
        st.error(f'Error summarizing transcript: {e}')
        st.stop()

    # Decode the response body.
    model_response_review = json.loads(response_review["body"].read())

    # Extract and print the response text.
    response_text_review = model_response_review["content"][0]["text"]
    st.info(response_text_review)
    st.session_state.llm_review_response = response_text_review

    # Clear up all customer data
    if (delete_files and file is not None):
        try:
            s3_resource = boto3.resource('s3')
            filename = key + conform_to_regex(file.name)
            s3_resource.Object(bucket_name, f'{filename}.json').delete()
            s3_resource.Object(bucket_name, f'{filename}').delete()
        except Exception as e:
            st.error(f'Error deleting files from S3: {e}')

    st.info(get_current_time())
    st.info("Please enter quip token, location, and name of the doc, and click 'Write Notes To Quip' to save the notes: ")

# Write Notes to Quip location

user_input_quip_accesstoken = st.text_input("Get Quip token from https://corp.quip-amazon.com/dev/token", type="password", key="QuipToken")
user_input_quip_folder_doc = st.text_input("Enter your Quip location (folder / doc): ", key="QuipLoc")
user_input_quip_doc_name = st.text_input("Enter your Quip document name: ", key="QuipDocName")

if st.button('Write Notes To Quip'):
    # Re-validate inputs
    if (user_input_meeting_notes == "" and file is None):
        st.info ("Please upload a meeting recording file, or your meeting notes to proceed...")
        st.stop()
    if (not st.session_state.fileTranscribed and user_input_meeting_notes == ""):
        st.info ("Please 'Submit Analysis' first...")
        st.stop()
    if st.session_state.llm_review_response == "":
        st.info ("Please 'Review Meeting Notes' first...")
        st.stop()
    if (user_input_quip_accesstoken == "" or user_input_quip_folder_doc == ""):
        st.info ("Please enter quip token and location...")
        st.stop()

    st.info("Writing to quip... " + get_current_time())
    # Define the prompt for the model.
    prompt_quip = SYSTEM_PROMPT_HTML + "\n" + TEMPLATE_FORMAT + "\n" + EXAMPLE_HTML + "\n" + user_input_prompt +": \n"  \
                    + st.session_state.llm_review_response
    # Format the request payload using the model's native structure.
    request_quip = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 10000,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt_quip}],
            }
        ],
    }

    # Convert the native request to JSON.
    request_quip = json.dumps(request_quip)

    try:
        # Invoke the model with the request.
        response_quip = client.invoke_model(modelId = model_id, body = request_quip)

    except Exception as e:
        st.error(f'Error summarizing transcript: {e}')
        st.stop()

    # Decode the response body.
    model_response_quip = json.loads(response_quip["body"].read())

    # Extract and print the response text.
    response_text_quip = model_response_quip["content"][0]["text"]
    #st.info(response_text_review)

    #Save the output to a quip document
    quip_token = user_input_quip_accesstoken
    quip_location = user_input_quip_folder_doc
    quip_doc_name = user_input_quip_doc_name

    try:
        # Call function to write LLM response to quip
        result = write_to_quip(quip_token, quip_doc_name, response_text_quip, quip_location)
        # Show results from the function
        st.info(result)
        st.info(get_current_time())
    except Exception as e:
        print(e)
    
#create a button to clear everything
if st.button('Clear Meeting Info'):
    st.session_state.fileUploaded = False
    st.session_state.fileTranscribed = False
    st.session_state.user_input_transcription = ""
    st.session_state.user_input_meeting_notes = ""
    st.session_state.user_input_attendees_agenda = ""
    file = None