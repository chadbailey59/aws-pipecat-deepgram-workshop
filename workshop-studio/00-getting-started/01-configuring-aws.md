# Setting up AWS

To complete this workshop, you'll need an AWS account.


## AWS Workshop Studio (for AWS-run events)


If you're attending an AWS-run event, follow these steps to access your pre-configured AWS account:

1. Open [AWS Workshop Studio](https://catalog.us-east-1.prod.workshops.aws/join/) .
2. Choose **Email OTP** as your sign-in method.

![Sign in](https://static.us-east-1.prod.workshops.aws/public/80e2f4fb-7fe5-4c2c-88fb-fb5de05b1533/static/images/sign-in.png)

3. Enter the event access code provided by the event organizer.

![Event access code](https://static.us-east-1.prod.workshops.aws/public/80e2f4fb-7fe5-4c2c-88fb-fb5de05b1533/static/images/event-access-code.png)

4. Read and agree to the _Terms and Conditions_ by selecting **I agree with the terms and conditions** and choose **Join Event**.

![Terms and conditions](https://static.us-east-1.prod.workshops.aws/public/80e2f4fb-7fe5-4c2c-88fb-fb5de05b1533/static/images/terms-and-condition.png)


### Accessing the AWS Console


1. In the left navigation at the bottom under AWS account access, click on **Open AWS Console**.

![Workshop - AWS Console](https://static.us-east-1.prod.workshops.aws/public/80e2f4fb-7fe5-4c2c-88fb-fb5de05b1533/static/images/workshop-studio-aws-console.png)

This will open the AWS Console in a new browser tab.


## Using Your Own AWS Account


If you're using your own AWS account, you'll need to set up the appropriate permissions:

1. Navigate to the IAM console.
2. Attach the **AdministratorAccess** policy to your IAM user or role.

Production Best Practice

For production environments, you should create and use more restrictive IAM policies that follow the principle of least privilege. The AdministratorAccess policy is used in this workshop for simplicity.
