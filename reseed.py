import boto3

COLLECTION_ID = 'face_sketch_collection'
rek = boto3.client('rekognition', region_name='us-east-1')

# 1) Delete old collection if it exists
try:
    rek.delete_collection(CollectionId=COLLECTION_ID)
    print("✅ Deleted old collection.")
except rek.exceptions.ResourceNotFoundException:
    print("ℹ️ No existing collection to delete.")
except Exception as e:
    print("⚠️ Warning deleting collection:", e)

# 2) Create a fresh one
rek.create_collection(CollectionId=COLLECTION_ID)
print("✅ Created fresh collection.")
