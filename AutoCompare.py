import numpy as np 
import cv2
import json
import boto3
from botocore.exceptions import ClientError
import logging

# Get the images from the user
# For now just get them from this directory


def processTextDetection(bucket, document):

    # Get the document from S3
    s3Connection = boto3.resource('s3')

    s3Object = s3Connection.Object(bucket, document)
    s3Response = s3Object.get()

def uploadImage(imageName, bucket, objectName=None):
    #Upload the image to the s3 bucket
    # Use objectName to define a custom file name for the s3 object

    if objectName is None:
        objectName = imageName

    # Upload the image
    s3Client = boto3.client('s3')
    try:
        response = s3Client.upload_file(imageName, bucket, objectName)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def main():
    image1 = 'handwrittentext.png'
    #image2 = 'image2.jpg'

    img1 = cv2.imread(image1, 1)
    #img2 = cv2.imread(image2, 1)

    bucket = 'writing-compare-sherwinvarkiani'
    uploadImage(image1, bucket)

    document = image1
    
    block_count = processTextDetection(bucket, document)
    print("Blocks detected: " + str(block_count))


if __name__ == "__main__":
    main()
