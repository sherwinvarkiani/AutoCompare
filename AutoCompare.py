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


    if len(text1indices) != len(text1) or len(text2indices) != len(text2):
        print("ERROR INDEX LENGTHS NOT EQUAL")
        print(len(text1indices), len(text1))
        print(len(text2indices), len(text2))

    # Difference checker
    counter = 0
    for i,s in enumerate(difflib.ndiff(text2,text1)):
        if s[0] == ' ': continue
        else:

            # Get the index and cast it to int
            index = text2indices[i-counter]
            if index != ' ':
                textIndex = int(index)
            else:
                continue

            # Get the polygon coordinates
            polygon = eval(text2Attributes['Polygon'][textIndex])
            # print(polygon, type(polygon))

            # print("Confidence: " + str(text2Attributes['Confidence'][textIndex]))
            color = (0,0,0)
            thickness = 3
            if s[0]=='-':
                # Delete (RED)
                counter += 1
                print(u'Delete "{}" from position {}'.format(s[-1],i-counter))

                # update text index
                del text2indices[i-counter]

                if float(text2Attributes['Confidence'][textIndex]) > 85:
                    color = (0,0,255) # red
                    thickness = 7
                else:
                    color = (255, 0, 255)
            elif s[0]=='+':

                print(u'Add "{}" to position {}'.format(s[-1],i-counter))  

                text2indices.insert(i-counter, textIndex)

                if float(text2Attributes['Confidence'][textIndex]) > 85:
                    color = (0,255,0) # green
                else:
                    color = (255, 255, 0)

            # print(polygon[3], type(polygon[3]))

            # Get the image height and width
            height, width, _ = img2.shape

            startPoint = (np.float32(polygon[3]['X'] * width), np.float32(polygon[3]['Y'] * height))
            endPoint = (np.float32(polygon[1]['X'] * width), np.float32(polygon[1]['Y'] * height))
            # print("STARTPOINT: " + str(startPoint))
            # print("ENDPOINT: " + str(endPoint))
            img2 = cv2.rectangle(img2, startPoint, endPoint, color, thickness)


    print("text1: " + str(text1))
    print("text2: " + str(text2))
    print("texta: " + str(text2indices))
    return img2


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
    image2 = 'editedText.jpg'

    # Read the images using opencv
    img1 = cv2.imread(image1, 1)
    img2 = cv2.imread(image2, 1)
    print("SIZE: " + str(img2.shape))
    img1 = cv2.resize(img1, (0,0), fx=0.5, fy=0.5)
    img2 = cv2.resize(img2, (0,0), fx=0.5, fy=0.5)

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

    img2 = compareText(text1Attributes, text2Attributes, img1, img2)


    cv2.imshow("Original", img1)
    cv2.imshow("Comparison", img2)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
