# Forensic Face Sketch Construction & Recognition

A Flask-based web application that lets forensic artists build facial sketches from selectable features, then upload sketches to find the best matching photograph using AWS Rekognition (with a local HOG-based fallback). Includes user registration, login, and email-based OTP authentication.

---

## 🚀 Features

- **User Authentication**  
  - **Register** with full name, email & password  
  - **Login** with email & password  
  - **OTP Verification**: one-time code sent to email on login/register

- **Sketch Construction**  
  - Drag-and-drop selectable facial features (eyes, nose, hair, etc.) to compose a sketch  
  - Save constructed sketches as PNG

- **Sketch Recognition**  
  - Upload a hand-drawn or constructed sketch  
  - Search matching face in an AWS Rekognition collection  
  - Display best match photo along with name, age, DOB, and SSIM similarity score  
  - Fallback to local HOG-feature matching if Rekognition returns no results (optional)

- **Data Persistence**  
  - Stores face metadata in DynamoDB (person_id, name, age, DOB, photo path, timestamp)  
  - Optional local pickle databases (`sketches_db.pkl` & `features_db.pkl`) for offline matching

---

## 🛠 Tech Stack

- **Backend**: Python 3.8+, Flask, Flask-Login, Flask-Mail  
- **Frontend**: HTML5, CSS3, JavaScript (drag-and-drop + html2canvas)  
- **AWS Services**:  
  - **Rekognition** (face indexing & search)  
  - **DynamoDB** (face metadata storage)  
- **Local Fallback**: OpenCV & scikit-image (HOG + SSIM)

---

## 📋 Prerequisites

- Python 3.8 or newer  
- AWS account with permissions for Rekognition & DynamoDB  
- AWS CLI configured locally (`aws configure`)  
- SMTP email account (e.g. Gmail) for OTP  
- (Optional) virtual environment tool (venv, pipenv, etc.)

---

## ⚙️ Installation & Setup

    git clone https://github.com/<your-username>/forensic-face-sketch.git
    cd forensic-face-sketch
    python3 -m venv venv
    source venv/bin/activate    # on Linux/macOS
    venv\Scripts\activate       # on Windows
    pip install -r requirements.txt

### AWS Rekognition & DynamoDB

    aws rekognition create-collection --collection-id face_sketch_collection --region us-east-1

Create a DynamoDB table named `FaceSketchData` with primary key `person_id` (String).

### Environment Variables

Create a `.env` file at the project root (or export in your shell):

    AWS_REGION=us-east-1
    REK_COLLECTION_ID=face_sketch_collection
    DDB_TABLE_NAME=FaceSketchData
    FLASK_SECRET_KEY=your_secret_key

    # Flask-Mail / OTP settings
    MAIL_SERVER=smtp.gmail.com
    MAIL_PORT=587
    MAIL_USE_TLS=True
    MAIL_USERNAME=your_email@gmail.com
    MAIL_PASSWORD=your_email_password

---

## 🚀 Running the App

    export FLASK_APP=app.py
    export FLASK_ENV=development  # optional: enables auto-reload & debug
    flask run

Open http://127.0.0.1:5000/ in your browser.

---

## 📂 Project Structure

    .
    ├── app.py
    ├── requirements.txt
    ├── templates/
    │   ├── index.html           # Home: login/register
    │   ├── register.html        # Registration form + OTP
    │   ├── login.html           # Login form
    │   ├── otp_verify.html      # Enter OTP
    │   ├── dashboard.html       # Create/Upload sketch menu
    │   ├── Face_Construct.html  # Sketch builder canvas
    │   ├── upload.html          # Sketch upload form
    │   ├── result.html          # Display match result or “no match”
    │   └── save_success.html    # Confirmation after indexing a new sketch
    ├── static/
    │   ├── uploads/             # Temporary uploaded sketches
    │   ├── photos/              # Known photos indexed in Rekognition
    │   └── assets/              # Sketch-feature PNGs (eyes, nose, etc.)
    ├── database/
    │   ├── sketches_db.pkl      # Local sketch metadata (fallback)
    │   └── features_db.pkl      # Local HOG-feature vectors (fallback)
    └── index_reference.py       # Helper to bulk-index reference photos

---

## 🤝 Contributing

1. Fork the repository  
2. Create a feature branch (`git checkout -b feature/XYZ`)  
3. Commit your changes (`git commit -m "Add XYZ"`)  
4. Push to your fork (`git push origin feature/XYZ`)  
5. Open a Pull Request

---

## 📜 License

MIT © Your Name

---

## 🙋‍ Questions?

Open an issue or contact me at `<mshourya9456@gmail.com>`.
