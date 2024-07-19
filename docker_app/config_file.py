class Config:
    # Stack name
    # Change this value if you want to create a new instance of the stack
    STACK_NAME = "Streamlit"
    
    # Put your own custom value here to prevent ALB to accept requests from
    # other clients that CloudFront. You can choose any random string.
    CUSTOM_HEADER_VALUE = "streamlit_demo_app_58dsv15e4s31"    
    
    # ID of Secrets Manager containing cognito parameters
    # When you delete a secret, you cannot create another one immediately
    # with the same name. Change this value if you destroy your stack and need
    # to recreate it with the same STACK_NAME.
    SECRETS_MANAGER_ID = f"{STACK_NAME}ParamCognitoSecret12345"

    # S3 Bucket name
    # Change this value if you want to create a new instance of the stack
    S3_BUCKET_NAME = f"{STACK_NAME.lower()}-meeting-summarizer"