import numpy as np
import cv2 as cv
from PIL import Image
import torch
from torchvision import models, transforms
import time
import urllib

# Download ImageNet labels, source: https://pytorch.org/hub/pytorch_vision_resnet/
# !wget https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt

# The below snippet was taken from here: https://pytorch.org/hub/pytorch_vision_resnet/
url, filename = ("https://github.com/pytorch/hub/raw/master/images/dog.jpg", "dog.jpg")
try: urllib.URLopener().retrieve(url, filename)
except: urllib.request.urlretrieve(url, filename)


def predict(imgPath):
    with open("imagenet_classes.txt", "r") as f:
        class_names = [s.strip() for s in f.readlines()]
    
    model = models.resnet50(pretrained=True)
    model.eval()
    print(class_names)
    transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
    mean=[0.485, 0.456, 0.406],
    std=[0.229, 0.224, 0.225]
    )])    
    img = Image.open(imgPath)
    input1 = torch.unsqueeze(transform(img), 0)
    output = model(input1)
    _, pred = torch.max(output, 1)

    return class_names[pred]