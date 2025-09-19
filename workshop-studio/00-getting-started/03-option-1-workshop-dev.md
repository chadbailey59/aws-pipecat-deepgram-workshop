# Option 1: Workshop dev

For this workshop, you have two options for your development environment:

1. **AWS Workshop Studio Environment** - For AWS-run events, use the pre-configured cloud-based VS Code Serve
    
2. **Local Development Environment** - Set up your own local environment with the required tools
    


## AWS Workshop Studio environment (for AWS-run events)

If you're attending an AWS-run event, we recommend using the provided cloud-based Visual Studio Code Server environment. This environment comes pre-configured with all the necessary tools and AWS credentials.


### Accessing Visual Studio Code server


1. In the [event page](https://prod.workshops.aws/event/dashboard/) , navigate to the **Event Outputs** pane at the bottom of the page.

![Workshop - Event Outputs](https://static.us-east-1.prod.workshops.aws/public/80e2f4fb-7fe5-4c2c-88fb-fb5de05b1533/static/images/event-output.png)

2. Copy the **Password**. You will need this in the next step.
3. Select the **URL**. Visual Studio Code Server will open in a new browser tab.
4. In the **Welcome to code-server** dialog, paste the password that you copied earlier, and choose **Submit**.

![VS Code Server Login](https://static.us-east-1.prod.workshops.aws/public/80e2f4fb-7fe5-4c2c-88fb-fb5de05b1533/static/images/vscodeserver-login.png)

You should now see the Visual Studio Code IDE in your browser.

![VS Code Server](https://static.us-east-1.prod.workshops.aws/public/80e2f4fb-7fe5-4c2c-88fb-fb5de05b1533/static/images/vscodeserver.png)


### Setting up Python virtual environment


Even though the Workshop Studio environment comes pre-configured, you'll need to set up a Python virtual environment for your project:

1. Open a terminal in VS Code by selecting **Terminal** > **New Terminal** from the menu.
    
2. Create a new directory for your project.
    
    ```
    mkdir -p voice-agent
    cd voice-agent
    ```
    
2. You'll need Python 3.12 or newer for this lab. You can check your existing version by running `python --version` in a terminal. If you have an older version of Python, you can install Python 3.12 by running:
    ```
    sudo dnf install -y python3.12
    ```
    The `sudo` password is the same password you used to log in to the VS Code cloud environment.

3. Create a virtual environment.
    
    ```
    # If you already have a new version of Python:
    python -m venv venv
    # If you had to install Python 3.12:
    python3.12 -m venv venv
    ```
    
4. Activate the virtual environment.
    
    ```
    source venv/bin/activate
    ```
    


### AWS Credentials in the Workshop Environment


The AWS Workshop Studio environment comes with AWS credentials pre-configured. You'll need those credentials for your .env file in a later step.

To run this lab in the cloud VS Code environment, you'll need to use the Daily transport, which means you'll need a Daily API key. If you're running this lab at an AWS event, you'll be given a Daily API key to use.

If you plan to deploy your bot to Pipecat Cloud, you can sign up for an account at [pipecat.daily.co](https://pipecat.daily.co). Your Pipecat account includes a Daily API key [in the dashboard](https://pipecat.daily.co/qventus-poc/settings/keys#daily).

If you're not deploying to Pipecat Cloud, you can sign up for a free Daily account at [daily.co](https://daily.co). You'll need to enter a credit card to get started, but you get plenty of free minutes to use with this lab.


## Next Steps


Now that you've accessed your development environment and set up your Python virtual environment, let's proceed.
