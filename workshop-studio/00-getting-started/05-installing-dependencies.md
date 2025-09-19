# Installing dependencies and creating your run script

Before you start building your voice AI agent, you need to install necessary dependencies and a run script so that you can iterate quickly.


## Install dependencies


Let's install all the required packages for building a voice AI agent with Amazon Nova Sonic and Pipecat:

```bash
pip install "pipecat-ai[webrtc,daily,silero,aws-nova-sonic]"==0.0.85 pipecat-ai-small-webrtc-prebuilt fastapi uvicorn python-dotenv boto3
```

Pipecat supports Amazon Nova Sonic from [version 0.0.67](https://github.com/pipecat-ai/pipecat/releases/tag/v0.0.67) onward.

1. Create a `.env` file in your project directory.
    
    ```
    touch .env
    ```
    
2. Add your AWS and Daily credentials to the `.env` file.
    
    ```
    AWS_ACCESS_KEY_ID=your_access_key_id
    AWS_SECRET_ACCESS_KEY=your_secret_access_key
    AWS_REGION=us-east-1
    DAILY_API_KEY=your_daily_api_key
    ```
    
3. Add your `.env` file to `.gitignore`.
    
    ```
    echo ".env" >> .gitignore
    ```

## Next steps

Now that you have set up your environment and created the run script, you're ready to start building your voice AI agent.
