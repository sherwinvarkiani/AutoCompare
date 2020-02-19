import numpy as np 
import cv2

import boto3
from botocore.exceptions import ClientError
import logging

# used for text differences
import difflib

# Get the images from the user
# For now just get them from this directory


def processTextDetection(bucket, document):

    # Get the document from S3
    s3Connection = boto3.resource('s3')

    s3Object = s3Connection.Object(bucket, document)
    s3Response = s3Object.get()

    # Detect the text in the image
    client = boto3.client('textract')

    # Process using S3 Object
    response = client.detect_document_text(Document={'S3Object': {'Bucket' : bucket, 'Name' : document}})

    # Get the text blocks
    blocks = response['Blocks']
    
    textAttributes = {}
    textList = []
    textConfidence = []
    textPolygon = []
    # Go through all the text blocks
    for block in blocks:
        if block['BlockType'] == "WORD":
            # If it detects a word add it to the dictionary and store the confidence
            textList.append(block['Text'])
            textConfidence.append("{:.2f}".format(block['Confidence']))
            textPolygon.append('{}'.format(block['Geometry']['Polygon']))

    textAttributes['Text'] = textList
    textAttributes['Confidence'] = textConfidence
    textAttributes['Polygon'] = textPolygon
    return textAttributes

def compareText(text1Attributes, text2Attributes):
    print("Comparing Texts")
    text1 = ""
    text2 = ""

    text1List = text1Attributes['Text']
    text2List = text2Attributes['Text']
    
    # Get all of the text
    for t in text1List:
        text1 += t + " "

    for t in text2List:
        text2 += t + " "
    
    for i,s in enumerate(difflib.ndiff(text1,text2)):
        if s[0] == ' ': continue
        elif s[0] == '-':
            # Delete (RED)
            print(u'Delete "{}" from position {}'.format(s[-1],i))
        elif s[0]=='+':
            # Add (GREEN)
            print(u'Add "{}" to position {}'.format(s[-1],i))  


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
    image2 = 'image2.jpg'

    # Read the images using opencv
    img1 = cv2.imread(image1, 1)
    img2 = cv2.imread(image2, 1)

    # S3 Bucket name
    bucket = 'writing-compare-sherwinvarkiani'

    # Upload the image to the bucket
    uploadImage(image1, bucket)
    document = image1

    # Use textract to get text from image
    text1Attributes = processTextDetection(bucket, document)
    print(text1Attributes)

    # # Upload the image to the bucket
    uploadImage(image2, bucket)
    document = image2

    # Use textract to get text from image
    text2Attributes = processTextDetection(bucket, document)


    


if __name__ == "__main__":
    main()
