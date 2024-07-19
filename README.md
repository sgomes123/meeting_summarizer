# deploy-streamlit-app

This app can be used as a starting point to easily create and deploy a GenAI demo, with web interface and user authentication. It is written in python only, with cdk template to deploy on AWS.

It deploys a basic Streamlit app, and contains the following components:

* The Streamlit app in ECS/Fargate, behind an ALB and CloudFront
* A Cognito user pool in which you can manage users

By default, the Streamlit app has the following features:

* Authentication through Cognito
* Connection to Bedrock 

## Architecture diagram

![Architecture diagram](img/archi_streamlit_cdk.png)

## Usage

In the docker_app folder, you will find the streamlit app. You can run it locally or with docker.

Note: for the docker version to run, you will need to give appropriate permissions to the container for bedrock access. This is not implemented yet.

In the main folder, you will find a cdk template to deploy the app on ECS / ALB.

Prerequisites:

* python3.8
* docker
* use a Chrome browser for development
* `anthropic.claude-v2` model activated in Amazon Bedrock in your AWS account
* the environment used to create this demo was an AWS Cloud9 m5.large instance with Amazon Linux 2023, but it should also work with other configurations

To deploy:

1. Edit `docker_app/config_file.py`, choose a `STACK_NAME` and a `CUSTOM_HEADER_VALUE`.

2. Install dependencies

To fix the "layer already exists" problem in Docker, you can try a few different approaches:

** Prune Docker system**: Sometimes, old or unused Docker layers can cause conflicts. You can prune your Docker system to remove these unused objects. Run the following command:
   ```
   docker system prune -a
   ```
   This will remove all unused containers, networks, images (both dangling and unreferenced), and optionally, volumes.

** Rebuild the image without cache**: Building the Docker image without using the cache can help resolve this issue. Use the `--no-cache` option with the `docker build` command:
   ```
   docker build --no-cache -t your_image_name .
   ```

** Clean up dangling images**: Dangling images can sometimes lead to layer conflicts. You can remove them with:
   ```
   docker image prune
   ```

** Remove specific image**: If the problem persists, you can try removing the specific image that is causing the conflict:
   ```
   docker rmi your_image_name
   ```

** Update Docker**: Ensure that you are using the latest version of Docker. Sometimes, updating Docker can resolve issues caused by bugs in older versions.
Try these steps one by one, and hopefully, the issue will be resolved. If the problem persists, it might be helpful to provide more details about the specific commands and Dockerfile you are using.
 
```
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

3. Deploy the cdk template

```
cdk bootstrap (cdk bootstrap aws://094128535270/us-east-1)
cdk deploy
```

The deployment takes 5 to 10 minutes.

Make a note of the output, in which you will find the CloudFront distribution URL
and the Cognito user pool id.

4. Create a user in the Cognito UserPool that has been created. You can perform this action from your AWS Console. 
5. From your browser, connect to the CloudFront distribution url.
6. Log in to the Streamlit app with the user you have created in Cognito.

## Testing and developing in Cloud9

After deployment of the cdk template containing the Cognito user pool required for authentication, you can test the Streamlit app directly from Cloud9.
You can either use docker, but this would require setting up a role with appropriate permissions, or run the Streamlit app directly in your terminal after having installed the required python dependencies.

To run the Streamlit app directly:

1. If you have activated a virtual env for deploying the cdk template, deactivate it:

```
deactivate
```

2. cd into the streamlit-docker directory, create a new virtual env, and install dependencies:

```
cd docker_app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Launch the streamlit server

```
streamlit run app.py --server.port 8080
```

4. Click on the Preview/Preview running application button in Cloud9, and click on the button to Pop out the browser in a new window, as the Cloud9 embedded browser does not keep session cookies, which prevents the authentication mechanism to work properly.
If the new window does not display the app, you may need to configure your browser to accept cross-site tracking cookies.

5. You can now modify the streamlit app to build your own demo!

## Some limitations

* The connection between CloudFront and the ALB is in HTTP, not SSL encrypted.
This means traffic between CloudFront and the ALB is unencrypted.
It is **strongly recommended** to configure HTTPS by bringing your own domain name and SSL/TLS certificate to the ALB.
* The provided code is intended as a demo and starting point, not production ready.
The Python app relies on third party libraries like Streamlit and streamlit-cognito-auth.
As the developer, it is your responsibility to properly vet, maintain, and test all third party dependencies.
The authentication and authorization mechanisms in particular should be thoroughly evaluated.
More generally, you should perform security reviews and testing before incorporating this demo code in a production application or with sensitive data.
* In this demo, Amazon Cognito is in a simple configuration.
Note that Amazon Cognito user pools can be configured to enforce strong password policies,
enable multi-factor authentication,
and set the AdvancedSecurityMode to ENFORCED to enable the system to detect and act upon malicious sign-in attempts.
* AWS provides various services, not implemented in this demo, that can improve the security of this application.
Network security services like network ACLs and AWS WAF can control access to resources.
You could also use AWS Shield for DDoS protection and Amazon GuardDuty for threats detection.
Amazon Inspector performs security assessments.
There are many more AWS services and best practices that can enhance security -
refer to the AWS Shared Responsibility Model and security best practices guidance for additional recommendations.
The developer is responsible for properly implementing and configuring these services to meet their specific security requirements.
* Regular rotation of secrets is recommended, not implemented in this demo.

## Acknowledgments

This code is inspired from:

* https://github.com/tzaffi/streamlit-cdk-fargate.git
* https://github.com/aws-samples/build-scale-generative-ai-applications-with-amazon-bedrock-workshop/

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This application is licensed under the MIT-0 License. See the LICENSE file.