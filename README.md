# Campus AI Assistant Server

This is the backend server for the Campus AI Assistant, providing schedule management and voice assistant capabilities.

## Deployment Instructions

### Option 1: Deploy to Heroku (Recommended)

1. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Login to Heroku:
   ```bash
   heroku login
   ```

3. Create a new Heroku app:
   ```bash
   heroku create your-app-name
   ```

4. Set up environment variables:
   ```bash
   heroku config:set SUPABASE_URL=your_supabase_url
   heroku config:set SUPABASE_KEY=your_supabase_key
   heroku config:set FLASK_ENV=production
   ```

5. Deploy the code:
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

Your app will be available at `https://your-app-name.herokuapp.com`

### Option 2: Deploy to DigitalOcean App Platform

1. Fork this repository to your GitHub account
2. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
3. Click "Create App" and select your GitHub repository
4. Configure environment variables:
   - SUPABASE_URL
   - SUPABASE_KEY
   - FLASK_ENV=production
5. Deploy the app

### Option 3: Run on a VPS (Advanced)

1. Get a VPS from DigitalOcean, AWS, or similar
2. SSH into your server
3. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   ```

4. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd <repo-directory>
   ```

5. Install Python dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

6. Set up systemd service:
   ```bash
   sudo nano /etc/systemd/system/campus-ai.service
   ```
   Add the following:
   ```ini
   [Unit]
   Description=Campus AI Assistant
   After=network.target

   [Service]
   User=<your-user>
   WorkingDirectory=/path/to/your/app
   Environment="PATH=/path/to/your/venv/bin"
   Environment="FLASK_ENV=production"
   Environment="SUPABASE_URL=your_supabase_url"
   Environment="SUPABASE_KEY=your_supabase_key"
   ExecStart=/path/to/your/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

   [Install]
   WantedBy=multi-user.target
   ```

7. Set up Nginx:
   ```bash
   sudo nano /etc/nginx/sites-available/campus-ai
   ```
   Add the following:
   ```nginx
   server {
       listen 80;
       server_name your_domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

8. Enable and start services:
   ```bash
   sudo ln -s /etc/nginx/sites-available/campus-ai /etc/nginx/sites-enabled/
   sudo systemctl start campus-ai
   sudo systemctl enable campus-ai
   sudo systemctl restart nginx
   ```

9. Set up SSL with Let's Encrypt:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your_domain.com
   ```

## Update Flutter App

After deploying, update your Flutter app's configuration:

1. Open your Flutter project
2. Find where the server URL is defined (likely in a config or constants file)
3. Update it to your new domain:
   ```dart
   static const String SERVER_URL = 'https://your-domain.com';
   ```

## Environment Variables

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon/public key
- `FLASK_ENV`: Set to 'production' in production
- `PORT`: Port number (optional, defaults to 5000)

## Security Notes

1. Always use HTTPS in production
2. Keep your Supabase keys secure
3. Consider implementing rate limiting
4. Monitor your application logs
5. Regularly update dependencies

## Setup Instructions

### 1. Firebase Setup

1. Create a new Firebase project at [Firebase Console](https://console.firebase.google.com)
2. Enable Authentication and Firestore in your project
3. Create a service account key:
   - Go to Project Settings > Service Accounts
   - Click "Generate New Private Key"
   - Save the JSON file as `firebase-credentials.json` in the project root

### 2. Backend Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Firebase Authentication:
- Enable Email/Password authentication in Firebase Console
- Create an admin user through Firebase Console

3. Set up Firestore Database:
- Create a collection named `users` with the following structure:
  ```
  users/
    {uid}/
      is_admin: boolean
      student_id: string
  ```
- Create a collection named `schedules` with the following structure:
  ```
  schedules/
    {document_id}/
      student_id: string
      class_name: string
      day_of_week: string
      start_time: string (HH:MM format)
      end_time: string (HH:MM format)
      room: string
      created_at: timestamp
  ```

4. Run the backend server:
```bash
python app.py
```

### 3. Frontend Setup

1. Update your Flutter app's `pubspec.yaml` to include Firebase packages:
```yaml
dependencies:
  firebase_core: ^latest_version
  firebase_auth: ^latest_version
  cloud_firestore: ^latest_version
```

2. Initialize Firebase in your Flutter app:
- Download the `google-services.json` (Android) and/or `GoogleService-Info.plist` (iOS) from Firebase Console
- Place them in the appropriate platform-specific directories
- Update your platform configurations as per Firebase Flutter setup guide

3. Run the Flutter app:
```bash
flutter run
```

## API Authentication

All API requests that require authentication should include a Firebase ID token in the Authorization header:
```
Authorization: Bearer <firebase_id_token>
```

## API Endpoints

### POST /process-voice
Process voice input and get AI-powered or schedule-based responses.

### POST /add-schedule (Admin only)
Add a new class schedule.

### DELETE /delete-schedule (Admin only)
Delete an existing class schedule.

## Security Rules

Implement these security rules in your Firestore:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if false;  // Admin only through backend
    }
    
    match /schedules/{scheduleId} {
      allow read: if request.auth != null;
      allow write: if false;  // Admin only through backend
    }
  }
}
``` 