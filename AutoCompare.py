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

def compareText(text1Attributes, text2Attributes, img1, img2):
    print("Comparing Texts")
    text1 = ""
    text1indices = []
    text2 = ""
    text2indices = []

    text1List = text1Attributes['Text']
    text2List = text2Attributes['Text']

    # Get all of the text
    for t in text1List:
        text1 += t + " "

        # Set up the corresponding indices for the words in the text
        for index in range(0,len(t)):
            text1indices.append(text1List.index(t))
        text1indices += " "

    for t in text2List:
        text2 += t + " "

        # Set up the corresponding indices for the words in the text
        for index in range(0,len(t)):
            text2indices.append(text2List.index(t))
        text2indices += " "
    
    print("text1: " + str(text1))
    print("text2: " + str(text2))

    if len(text1indices) != len(text1) or len(text2indices) != len(text2):
        print("ERROR INDEX LENGTHS NOT EQUAL")
        print(len(text1indices), len(text1))
        print(len(text2indices), len(text2))

    for i,s in enumerate(difflib.ndiff(text2,text1)):
        if s[0] == ' ': continue
        elif s[0] == '-':
            # Delete (RED)
            print(u'Delete "{}" from position {}'.format(s[-1],i))

            # Get the index and cast it to int
            index = text2indices[i]
            if index != ' ':
                textIndex = int(index)
            else:
                continue

            # Get the polygon coordinates
            polygon = text2Attributes['Polygon'][textIndex]
            print(polygon)

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
    image1 = 'testImage.png'
    image2 = 'testImage2.png'

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
    # print(text1Attributes)

    # # Upload the image to the bucket
    uploadImage(image2, bucket)
    document = image2

    # Use textract to get text from image
    text2Attributes = processTextDetection(bucket, document)

    compareText(text1Attributes, text2Attributes, img1, img2)


    


if __name__ == "__main__":
    main()
