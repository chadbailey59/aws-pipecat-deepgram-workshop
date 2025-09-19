# Option 2: Local dev

If you prefer to use your own local development environment instead of the AWS Workshop Studio environment, follow these steps to set up everything you need.


## Prerequisites


Before you start building your voice AI agent, ensure you have:

- Python 3.12 or higher installed
- AWS CLI installed and configured

Python Version Requirement

This workshop requires Python 3.12 or higher. Earlier versions will not work with the dependencies and libraries used in this workshop. Please verify your Python version before proceeding.


## Set up your development environment


1. Create a new directory for your project.
    
    ```
    mkdir -p voice-agent
    cd voice-agent
    ```
    
2. Create a virtual environment.
    
    ```
    python -m venv venv
    ```
    
3. Activate the virtual environment.
    

- On macOS/Linux:
    
    ```
    source venv/bin/activate
    ```
    
- On Windows:
    
    ```
    venv\Scripts\activate
    ```
    

4. Install required dependencies.
    
    ```
    pip install boto3 python-dotenv
    ```
    


## Configure AWS credentials


Workshop Credentials

If you're attending an AWS-hosted workshop event, you can retrieve your AWS credentials from the [Event Dashboard](https://prod.workshops.aws/event/dashboard/en-US)  under the "Event Outputs" section. You'll find your `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` there.

1. Create a `.env` file in your project directory.
    
    ```
    touch .env
    ```
    
2. Add your AWS credentials to the `.env` file.
    
    ```
    AWS_ACCESS_KEY_ID=your_access_key_id
    AWS_SECRET_ACCESS_KEY=your_secret_access_key
    AWS_REGION=us-east-1
    ```
    
3. Add your `.env` file to `.gitignore`.
    
    ```
    echo ".env" >> .gitignore
    ```
    


## Verify your setup


1. Create a test file named `test_setup.py`.
    
    ```
    touch test_setup.py
    ```
    
2. Add the following code to `test_setup.py`.
    
    ```python
    # test_setup.py
    import os
    import boto3
    import sys
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Check Python version
    python_version = sys.version_info
    required_version = (3, 12)
    
    print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version.major < required_version[0] or (python_version.major == required_version[0] and python_version.minor < required_version[1]):
        print(f"WARNING: Python {required_version[0]}.{required_version[1]} or higher is required for this workshop.")
        print(f"Your version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        print("Please upgrade your Python version before proceeding.")
    else:
        print(f"Python version check passed! You have {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check if AWS credentials are available
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region = os.getenv("AWS_REGION")
    
    if aws_access_key and aws_secret_key and aws_region:
        print("AWS credentials found!")
        print(f"Region: {aws_region}")
        
        # Try to get AWS account information
        try:
            sts_client = boto3.client('sts')
            account_info = sts_client.get_caller_identity()
            print(f"Successfully connected to AWS!")
            print(f"Account ID: {account_info['Account']}")
            print(f"User ARN: {account_info['Arn']}")
        except Exception as e:
            print(f"Error connecting to AWS: {e}")
    else:
        print("AWS credentials missing. Please check your .env file.")
    ```
    
3. Run the test script.
    
    ```
    python test_setup.py
    ```
    

If your setup is correct, you should see:

```
Python version: 3.12.0
Python version check passed! You have 3.12.0
AWS credentials found!
Region: us-east-1
Successfully connected to AWS!
Account ID: 123456789012
User ARN: arn:aws:iam::123456789012:user/workshop-user
```

If you see a Python version warning, you'll need to upgrade your Python version before continuing with the workshop.


## Next Steps

Now that you've set up your development environment and set up your Python virtual environment, let's proceed.
