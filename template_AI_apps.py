import streamlit as st
from PIL import Image
import numpy as np
from model import predict
import time
import cv2 as cv

# source: jason-leung from unsplash
logo = "./jason-leung-1DjbGRDh7-E-unsplash.jpg"
image = Image.open(logo)
img_logo = np.array(image) 
img_shape = (280, 420)
img_logo = cv.resize(img_logo, img_shape, interpolation=cv.INTER_AREA)
st.image(img_logo)

'''
# Prototype App for Image Classification
'''

img_file_buffer = st.file_uploader("Upload an image")
if img_file_buffer is not None:
    image = Image.open(img_file_buffer)
    imageLocation = st.empty()
    image = np.array(image) 
    imageLocation.image(image, caption="Image", use_column_width=True)
    print("Classifying...")
    classification_label_Location = st.empty()
    classification_label_Location.write("Classifying....")
    imageLocation.image(image)
    start = time.time()
    label = predict(img_file_buffer)
    label = label.upper()
    classification_label_Location.write(f"Classification: {label}")
    end = time.time()
    infTime = end - start
    print(f"Inference time: {infTime}")
