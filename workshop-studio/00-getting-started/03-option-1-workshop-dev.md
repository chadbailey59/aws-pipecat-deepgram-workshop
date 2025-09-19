# Option 1: Workshop dev

For this workshop, you have two options for your development environment:

1. **AWS Workshop Studio Environment** - For AWS-run events, use the pre-configured cloud-based VS Code Serve
    
2. **Local Development Environment** - Set up your own local environment with the required tools
    


## AWS Workshop Studio environment (for AWS-run events)


Currently under construction!

The workshop studio environment is currently under construction. Please use your local dev in the meantime. If you have any questions, please contact Daniel Wirjo ([wirjo@amazon.com](mailto:wirjo@amazon.com) ).

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
    
3. Create a virtual environment.
    
    ```
    python -m venv venv
    ```
    
4. Activate the virtual environment.
    
    ```
    source venv/bin/activate
    ```
    


### AWS Credentials in the Workshop Environment


The AWS Workshop Studio environment comes with AWS credentials pre-configured. You don't need to set up any additional credentials to get started.


## Next Steps


Now that you've accessed your development environment and set up your Python virtual environment, let's proceed.
