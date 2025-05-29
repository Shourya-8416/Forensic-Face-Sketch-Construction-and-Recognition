import boto3
from datetime import datetime

# AWS Services
rekognition_client = boto3.client('rekognition', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('FaceSketchData')
COLLECTION_ID = 'face_sketch_collection'

# Ensure Rekognition Collection Exists
def create_collection():
    try:
        rekognition_client.create_collection(CollectionId=COLLECTION_ID)
        print("Collection created.")
    except rekognition_client.exceptions.ResourceAlreadyExistsException:
        print("Collection already exists.")

        

# Index Reference Face
def index_reference(image_path, person_id, name, dob, age, photo_path):
    """Index reference image in AWS Rekognition & store details in DynamoDB."""
    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    rekognition_client.index_faces(
        CollectionId=COLLECTION_ID,
        Image={'Bytes': image_bytes},
        ExternalImageId=person_id
    )

    table.put_item(Item={
        'person_id': person_id,
        'name': name,
        'dob': dob,
        'age' : age,
        'photo_path': photo_path,  # e.g., '2.jpg'
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

    print(f"✅ Indexed {name} (ID: {person_id}) in Rekognition & DynamoDB.")

if __name__ == '__main__':
    create_collection()

    people = [
       
        {'filename': 'Manjula B M.jpg', 'id': 'person_0001', 'name': 'Manjula B M', 'dob': 'Unknown', 'age': ''},
        {'filename': 'Pramodhini R.jpg', 'id': 'person_0002', 'name': 'Pramodhini R', 'dob': 'Unknown', 'age': ''},
        {'filename': 'Rekha Phadke.jpg', 'id': 'person_0003', 'name': 'Rekha Phadke', 'dob': 'Unknown', 'age': ''},
        {'filename': 'Rajani R.jpg', 'id': 'person_0004', 'name': 'Rajani R', 'dob': 'Unknown', 'age': ''},
        {'filename': 'Subhra Chakraborty.jpg', 'id': 'person_0005', 'name': 'Subhra Chakraborty', 'dob': 'Unknown', 'age': ''},
        {'filename': 'virat_kohli.jpg', 'id': 'person_0006', 'name': 'Virat Kolhi', 'dob': '1952-01-18', 'age': ''},
        {'filename': 'Dawood5.jpg', 'id': 'person_0011', 'name': 'Dawood Ibrahim', 'dob': '1955-12-26', 'age': ''},
        {'filename': 'Arya.jpg', 'id': 'person_0012', 'name': 'Manoj Kumar', 'dob': '1987-12-26', 'age': '38'},
        {'filename': 'Osama3.jpg', 'id': 'person_0013', 'name': 'Osama Bin Laden', 'dob': '1957-03-10', 'age': ''}    

    ]

    for person in people:
        image_path = f"static/photos/{person['filename']}"
        index_reference(
            image_path=image_path,
            person_id=person['id'],
            name=person['name'],
            dob=person['dob'],
            age=person['age'],
            photo_path=person['filename']
        )

