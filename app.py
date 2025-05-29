import os
import pickle
import random
from datetime import datetime, timedelta

import cv2
import numpy as np
import boto3
from skimage.metrics import structural_similarity as compare_ssim

from flask import (
    Flask, render_template, request, session,
    redirect, url_for, flash, send_from_directory
)
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required, logout_user
)
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from helpers import get_mac, get_ip_and_adapter


app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# — Mail (Gmail SMTP) —
app.config.update(
    MAIL_SERVER   = "smtp.gmail.com",
    MAIL_PORT     = 587,
    MAIL_USE_TLS  = True,
    MAIL_USERNAME = "forensic.face.tool@gmail.com",
    MAIL_PASSWORD = "iwqh puhe ryod xmkk"
)
mail = Mail(app)

# — DynamoDB Tables —
dynamodb     = boto3.resource("dynamodb", region_name="us-east-1")
users_table  = dynamodb.Table("Users")
face_table   = dynamodb.Table("FaceSketchData")

# — Rekognition —
rekognition_client = boto3.client("rekognition", region_name="us-east-1")
COLLECTION_ID       = "face_sketch_collection"

# — Flask-Login setup —
login_manager            = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = None


class User(UserMixin):
    def __init__(self, email, name=""):
        self.id   = email
        self.name = name

@login_manager.user_loader
def load_user(email):
    resp = users_table.get_item(Key={"email": email})
    item = resp.get("Item")
    return item and User(email=item["email"], name=item.get("name",""))

def send_otp(to_email, otp):
    msg = Message(
        subject="Your OTP",
        sender=app.config["MAIL_USERNAME"],
        recipients=[to_email]
    )
    msg.body = f"Your login OTP is {otp}. It expires in 5 minutes."
    mail.send(msg)




def index_local_photos():
    for item in table.scan().get('Items', []):
        pid      = item['person_id']
        filename = item.get('photo_path')
        if not filename:
            continue
        photo_fp = os.path.join('static', 'photos', filename)
        if os.path.exists(photo_fp):
            print(f"Indexing {filename} as {pid}")
            index_face_in_rekognition(photo_fp, pid)
        else:
            print(f"Missing photo file: {photo_fp}")


rekognition_client = boto3.client('rekognition', region_name='us-east-1')
COLLECTION_ID = 'face_sketch_collection'

def create_collection(collection_id):
    try:
        response = rekognition_client.create_collection(CollectionId=collection_id)
        print("Collection created:", response)
    except rekognition_client.exceptions.ResourceAlreadyExistsException:
        print("Collection already exists")

create_collection(COLLECTION_ID)


# Use DynamoDB to store extra face details (name, dob, age, photo_path, etc.)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
TABLE_NAME = 'FaceSketchData'  # Make sure this table exists with primary key 'person_id'
table = dynamodb.Table(TABLE_NAME)



def store_face_details(person_id, name, dob, age, photo_path):
    response = table.put_item(
        Item={
            'person_id': person_id,
            'name': name,
            'dob': dob,
            'age': age,
            'photo_path': photo_path,  # Relative path to image in static/photos/
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    )
    print("DynamoDB store response:", response)
    return response

def get_face_details(person_id):
    response = table.get_item(Key={'person_id': person_id})
    return response.get('Item', None)


UPLOAD_FOLDER = 'static/uploads'
DATABASE_FOLDER = 'database'
SKETCHES_DB = os.path.join(DATABASE_FOLDER, 'sketches_db.pkl')
FEATURES_DB = os.path.join(DATABASE_FOLDER, 'features_db.pkl')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATABASE_FOLDER, exist_ok=True)
os.makedirs('static/photos', exist_ok=True)  # For known photos (e.g., some_person.jpg)

# Initialize local pickle databases if not present (for fallback matching)
for db_path in [SKETCHES_DB, FEATURES_DB]:
    if not os.path.exists(db_path):
        with open(db_path, 'wb') as f:
            pickle.dump({}, f)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_features(image_path):
    """Extract HOG features from the image for local fallback matching."""
    img = cv2.imread(image_path, 0)  # grayscale
    img = cv2.resize(img, (128, 128))
    hog = cv2.HOGDescriptor((128, 128), (16, 16), (8, 8), (8, 8), 9)
    return hog.compute(img)

def save_to_local_database(person_id, name, features, sketch_path):
    """Save basic sketch info to local pickle DBs (optional fallback)."""
    with open(SKETCHES_DB, 'rb') as f:
        sketches_db = pickle.load(f)
    sketches_db[person_id] = {
        'name': name,
        'path': os.path.basename(sketch_path),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(SKETCHES_DB, 'wb') as f:
        pickle.dump(sketches_db, f)

    with open(FEATURES_DB, 'rb') as f:
        features_db = pickle.load(f)
    features_db[person_id] = features
    with open(FEATURES_DB, 'wb') as f:
        pickle.dump(features_db, f)
    return True

def index_face_in_rekognition(image_path, person_id):
    """Index the face/sketch in AWS Rekognition."""
    with open(image_path, 'rb') as image_file:
        image_bytes = image_file.read()
    response = rekognition_client.index_faces(
        CollectionId=COLLECTION_ID,
        Image={'Bytes': image_bytes},
        ExternalImageId=person_id,
        DetectionAttributes=['DEFAULT']
    )
    print("Index face response:", response)
    return response

def search_face_in_rekognition(image_path):
    """Search for a matching face using AWS Rekognition."""
    with open(image_path, 'rb') as image_file:
        image_bytes = image_file.read()
    response = rekognition_client.search_faces_by_image(
        CollectionId=COLLECTION_ID,
        Image={'Bytes': image_bytes},
        MaxFaces=1,
        FaceMatchThreshold=20  # Adjust threshold as needed
    )
    print("Search face response:", response)
    return response

def get_match_from_local_db(person_id):
    with open(SKETCHES_DB, 'rb') as f:
        sketches_db = pickle.load(f)
    return sketches_db.get(person_id, None)

def local_fallback_match(features):
    """Perform local matching based on HOG features as a fallback."""
    with open(FEATURES_DB, 'rb') as f:
        features_db = pickle.load(f)
    if not features_db:
        return None, None
    best_pid = None
    best_score = float('inf')
    for pid, stored_features in features_db.items():
        distance = np.linalg.norm(features - stored_features)
        if distance < best_score:
            best_score = distance
            best_pid = pid
    threshold = 1000  # Tune this threshold based on your data
    if best_score < threshold:
        return best_pid, best_score
    return None, None

def calculate_ssim(imageA_path, imageB_path):
    imageA = cv2.imread(imageA_path, cv2.IMREAD_GRAYSCALE)
    imageB = cv2.imread(imageB_path, cv2.IMREAD_GRAYSCALE)
    
    if imageA is None or imageB is None:
        return None

    imageA = cv2.resize(imageA, (256, 256))
    imageB = cv2.resize(imageB, (256, 256))

    score, _ = compare_ssim(imageA, imageB, full=True)
    return round(score * 100, 2)    


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name    = request.form["name"].strip()
        email   = request.form["email"].lower().strip()
        pwd     = request.form["password"]
        confirm = request.form["confirm_password"]

        if pwd != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        if users_table.get_item(Key={"email": email}).get("Item"):
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for("login"))

        users_table.put_item(Item={
            "email":         email,
            "password_hash": generate_password_hash(pwd),
            "name":          name
        })
        flash("Account created! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


from flask import make_response

@app.route("/login", methods=["GET", "POST"])
def login():
    mac = get_mac()
    ip, adapter = get_ip_and_adapter()

    # ─── Step 0: If already in OTP mode and it's a GET, resend a fresh OTP ───
    if request.method == "GET" and session.get("otp_required"):
        otp = f"{random.randint(0,999999):06d}"
        session["otp"] = otp
        session["otp_expires"] = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        send_otp(session["pending_email"], otp)
        flash("A new OTP has been sent to your email.", "info")

    # ─── Step 1: Email + Password submission ────────────────────────────────
    if request.method == "POST" and not session.get("otp_required"):
        email = request.form["email"].strip().lower()
        pwd   = request.form["password"]

        try:
            resp = users_table.get_item(Key={"email": email})
            user = resp.get("Item")
        except Exception:
            flash("Unable to reach user database. Try again later.", "danger")
            return redirect(url_for("login"))

        if not (user and check_password_hash(user["password_hash"], pwd)):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        otp = f"{random.randint(0,999999):06d}"
        session.update({
            "otp_required":  True,
            "pending_email": email,
            "otp":           otp,
            "otp_expires":   (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        })
        send_otp(email, otp)
        flash("OTP sent to your email.", "info")
        return redirect(url_for("login"))

    # ─── Step 2: OTP Verification ────────────────────────────────────────────
    if request.method == "POST" and session.get("otp_required"):
        if datetime.utcnow() > datetime.fromisoformat(session["otp_expires"]):
            session.clear()
            flash("OTP expired; please log in again.", "warning")
            return redirect(url_for("login"))

        if request.form["otp"].strip() != session["otp"]:
            flash("Wrong OTP. Please try again.", "danger")
            return redirect(url_for("login"))

        login_user(load_user(session["pending_email"]))
        for key in ["otp_required", "pending_email", "otp", "otp_expires"]:
            session.pop(key, None)
        return redirect(url_for("home"))

    # ─── GET (first load) or after redirect: render the page ────────────────
    resp = make_response(render_template(
        "login.html",
        mac=mac, ip=ip, adapter=adapter,
        otp_required=session.get("otp_required", False),
        pending_email=session.get("pending_email", "")
    ))
    # Prevent caching so back/refresh always re-invokes this view
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"]        = "no-cache"
    return resp


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def home():
    # in recognize_sketch view
    return render_template('index.html',
        match_found=False,
        
    )




@app.route('/construct_sketch')
def construct_sketch():
    # Sketch creation page (renders templates/Face_Construct.html)
    return render_template('Face_Construct.html')

@app.route('/upload')
def upload_page():
    # Upload page (renders templates/upload.html)
    return render_template('upload.html')


@app.route('/recognize_sketch', methods=['GET', 'POST'])
def recognize_sketch():
    # Allow GET to redirect to upload page to avoid 405 error
    if request.method == 'GET':
        return redirect(url_for('upload_page'))
    
    # Handle POST request from the upload form
    if 'sketch' not in request.files:
        flash('No file part in the request.')
        return redirect(url_for('upload_page'))
    
    file = request.files['sketch']
    if file.filename == '':
        flash('No file selected.')
        return redirect(url_for('upload_page'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}.png")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 1. Try AWS Rekognition first
        rekog_resp = search_face_in_rekognition(filepath)
        face_matches = rekog_resp.get('FaceMatches', [])
        print("DEBUG rekognition response:", rekog_resp)
        if face_matches:
            best_match = face_matches[0]
            similarity = best_match.get('Similarity', 0)
            person_id = best_match['Face'].get('ExternalImageId')
            if person_id:
        # Retrieve extra details from DynamoDB
                details = get_face_details(person_id)
                if details:
                    details['sketch_path'] = filename
                    details['similarity'] = round(similarity, 2)
                    details['interpretation'] = (
                        'High Confidence Match' if similarity >= 75
                        else 'Possible Match' if similarity >= 50
                        else 'Low Confidence Match'
                    )
                    return render_template('result.html', result=details, match_found=True)

        
        # # 2. Local fallback using HOG features
        # hog_features = extract_features(filepath)
        # local_pid, local_score = local_fallback_match(hog_features)
        # if local_pid:
        #     details = get_face_details(local_pid)
        #     if details:
        #         details['sketch_path'] = filename
        #         # Convert local distance to a similarity measure (example conversion)
        #         similarity_calc = max(0, 100 - (local_score / 10))
        #         details['similarity'] = round(similarity_calc, 2)
        #         details['interpretation'] = 'Likely the same person' if similarity_calc > 50 else 'Uncertain match'
        #         return render_template('result.html', result=details, match_found=True)
        
        # 3. No match found
        return render_template('result.html', match_found=False, uploaded_image=filename)
    
    flash('Invalid file type.')
    return redirect(url_for('upload_page'))

@app.route('/save_sketch', methods=['POST'])
def save_sketch():
    # Called from Face_Construct.html (for creating a new sketch entry)
    if 'sketchImage' not in request.files:
        flash('No sketch data found.')
        return redirect(url_for('construct_sketch'))
    
    file = request.files['sketchImage']
    if file.filename == '':
        flash('No file selected.')
        return redirect(url_for('construct_sketch'))
    
    if file and allowed_file(file.filename):
        person_name = request.form.get('personName', 'Unknown')
        dob = request.form.get('dob', 'Unknown')
        age = request.form.get('age', 'Unknown')
        person_id = f"person_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        filename = secure_filename(f"{person_id}.png")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        features = extract_features(filepath)
        # Index the sketch in Rekognition
        index_face_in_rekognition(filepath, person_id)
        # Save in local pickle DBs as fallback
        save_to_local_database(person_id, person_name, features, filepath)
        # Store additional details in DynamoDB
        # photo_path should point to an image file in static/photos/ for the matched photo
        photo_path = f"{person_id}.jpg"  # Update this as needed
        store_face_details(person_id, person_name, dob, age, photo_path)
        
        return render_template('save_success.html', name=person_name, id=person_id)
    
    flash('Invalid file type.')
    return redirect(url_for('construct_sketch'))

@app.route('/view_database')
def view_database():
    # Optional route to view local database (for debugging)
    with open(SKETCHES_DB, 'rb') as f:
        sketches_db = pickle.load(f)
    return render_template('database.html', sketches=sketches_db)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# index_local_photos()
if __name__ == '__main__':
    app.run(debug=True)






