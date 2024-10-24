# Developer details: 
        # Name: Tanisha Priya
        # Role: Architects
    # Version:
        # Version: V 1.0 (19 October 2024)
            # Developers: Tanisha Priya
            # Unit test: Pass
            # Integration test: Pass
     
    # Description: This code snippet uses YoloV8 Model to train, evaluate, and predict whether 
    # a person is wearing a mask, not wearing a mask, or is wearing in an incorrect manner.

# CODE - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    # Dependency: 
        # Environment:     
            # Python 3.11.5
            # Streamlit 1.36.0
import streamlit as st
import os
import shutil
import numpy as np
import xml.etree.ElementTree as ET
import yaml
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split
from ultralytics import YOLO
import matplotlib.pyplot as plt  # For plotting graphs
import seaborn as sns  # For heatmap visualization


# Data Preprocessing Functions
def create_folder_structure(base_path):
    folders = [
        'data/train/images', 'data/train/labels',
        'data/val/images', 'data/val/labels',
        'data/test/images', 'data/test/labels',
        'data/superval/images', 'data/superval/labels'
    ]
    for folder in folders:
        os.makedirs(os.path.join(base_path, folder), exist_ok=True)

def convert_bbox(size, box):
    dw = 1. / size[0]
    dh = 1. / size[1]
    x = (box[0] + box[2]) / 2.0
    y = (box[1] + box[3]) / 2.0
    w = box[2] - box[0]
    h = box[3] - box[1]
    return (x * dw, y * dh, w * dw, h * dh)

def convert_annotation(xml_path, output_path, classes):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    size = root.find('size')
    w = int(size.find('width').text)
    h = int(size.find('height').text)

    with open(output_path, 'w') as out_file:
        for obj in root.iter('object'):
            cls = obj.find('name').text
            if cls not in classes:
                continue
            cls_id = classes.index(cls)
            xmlbox = obj.find('bndbox')
            b = (float(xmlbox.find('xmin').text), float(xmlbox.find('ymin').text),
                 float(xmlbox.find('xmax').text), float(xmlbox.find('ymax').text))
            bb = convert_bbox((w, h), b)
            out_file.write(f"{cls_id} {' '.join(map(str, bb))}\n")

def process_images(image_files, image_folder, annotation_folder, output_path, split, classes):
    for file in image_files:
        # Image
        src_img = os.path.join(image_folder, file)
        dst_img = os.path.join(output_path, f'data/{split}/images', file)
        shutil.copy(src_img, dst_img)

        # Annotation
        xml_file = os.path.splitext(file)[0] + '.xml'
        src_xml = os.path.join(annotation_folder, xml_file)
        dst_txt = os.path.join(output_path, f'data/{split}/labels', os.path.splitext(file)[0] + '.txt')
        convert_annotation(src_xml, dst_txt, classes)

def split_and_process_dataset(image_files, image_folder, annotation_folder, output_path, classes):
    train_val, test = train_test_split(image_files, test_size=0.2, random_state=42)
    train, val_superval = train_test_split(train_val, test_size=0.25, random_state=42)  # 20% for val and superval combined
    val, superval = train_test_split(val_superval, test_size=0.5, random_state=42)      # 50% val, 50% superval

    for split, files in [('train', train), ('val', val), ('test', test), ('superval', superval)]:
        process_images(files, image_folder, annotation_folder, output_path, split, classes)

def create_yaml(output_path, classes):
    yaml_content = {
        'train': f'{os.getcwd()}/Data/train/images',
        'val': f'{os.getcwd()}/Data/val/images',
        'test': f'{os.getcwd()}/Data/test/images',
        'superval': f'{os.getcwd()}/Data/superval/images',
        'nc': len(classes),
        'names': classes
    }

    with open(os.path.join(output_path, 'data', 'data.yaml'), 'w') as yaml_file:
        yaml.dump(yaml_content, yaml_file, default_flow_style=False)


        
# Function to train the YOLOv8 model with only model_path as parameter
def train_yolov8_model(model_path, epochs=1, batch_size=32, img_size=640):
    # Load necessary paths and data
    data_yaml = f'{os.getcwd()}/Data/data.yaml'  # Assuming the YAML is in the 'Data' folder

    # Initialize YOLOv8 model
    model = YOLO('yolov8s.pt')

    # Train the model
    model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        plots=True,
    )

    # Evaluate the model after training using the test data specified in data.yaml
    results = model.val(data=data_yaml)

    # Extract evaluation metrics
    accuracy = results.metrics['accuracy']
    precision = results.metrics['precision']
    recall = results.metrics['recall']
    f1 = results.metrics['f1']
    conf_matrix = results.metrics['confusion_matrix']

    # Call the visualization function
    visualize_evaluation_metrics(accuracy, precision, recall, f1, conf_matrix)

    # Print evaluation metrics
    print(f"Accuracy: {accuracy}")
    print(f"Precision: {precision}")
    print(f"Recall: {recall}")
    print(f"F1-Score: {f1}")
    print(f"Confusion Matrix:\n{conf_matrix}")

    # Save the trained model
    save_model(model, model_path)

    # return model 
    return accuracy,precision,recall,f1


# Using the model.val() method to evaluate the model on the test set
def evaluate_yolov8_model(model, data_yaml):
    results = model.val(data=data_yaml)  # Automatically uses the test set in data.yaml

    # Extract metrics from results
    accuracy = results['metrics']['accuracy']
    precision = results['metrics']['precision']
    recall = results['metrics']['recall']
    f1 = results['metrics']['f1']
    conf_matrix = results['confusion_matrix']

    return accuracy, precision, recall, f1, conf_matrix

# Function to save the model
def save_model(model, model_path):
    model.save(model_path)
    


# Visualization function for evaluation metrics and confusion matrix
def visualize_evaluation_metrics(accuracy, precision, recall, f1, conf_matrix):
    # Bar plot for Accuracy, Precision, Recall, F1-Score
    metrics = {'Accuracy': accuracy, 'Precision': precision, 'Recall': recall, 'F1-Score': f1}
    metric_names = list(metrics.keys())
    metric_values = list(metrics.values())

    plt.figure(figsize=(10, 6))
    plt.bar(metric_names, metric_values, color=['skyblue', 'orange', 'green', 'red'])
    plt.ylim(0, 1)
    plt.title('Evaluation Metrics')
    plt.ylabel('Score')
    plt.show()

    # Confusion Matrix plot
    plt.figure(figsize=(8, 6))
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues')
    plt.title('Confusion Matrix')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.show()
