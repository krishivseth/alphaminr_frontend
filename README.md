# Alphaminr Frontend - Editor Portal

The frontend editor portal for the Alphaminr Newsletter Generator. This provides a clean, user-friendly interface for managing newsletters.

## 🎯 Features

- **Newsletter Generation Interface** - Generate newsletters via Railway backend
- **Newsletter Editor** - Edit and modify generated newsletters
- **Mailchimp Integration** - Send newsletters to subscribers
- **AI Review** - Get AI-powered feedback on newsletter content
- **GitHub Integration** - Version control for newsletters
- **Password Protection** - Secure editor access

## 🚀 Deployment

### Deploy to Vercel

1. **Connect Repository**:
   - Go to [Vercel.com](https://vercel.com)
   - Sign in with GitHub
   - Click "New Project"
   - Import this repository

2. **Set Environment Variables**:
   - Go to your project settings in Vercel
   - Navigate to "Environment Variables" section
   - Add the following variables:
     - `RAILWAY_BACKEND_URL` - Your Railway backend URL (e.g., `https://your-app.railway.app`)
     - `EDITOR_PASSWORD` - Password for editor access
     - `SECRET_KEY` - Flask secret key (generate a random string)
     - `MAILCHIMP_API_KEY` - Mailchimp API key (optional)
     - `MAILCHIMP_SERVER_PREFIX` - Mailchimp server prefix (optional)
     - `MAILCHIMP_LIST_ID` - Mailchimp list ID (optional)
     - `ANTHROPIC_API_KEY` - Anthropic API key (for AI review)

3. **Deploy**:
   - Vercel will automatically detect the Python app
   - It will install dependencies and start the server

## 🔧 Local Development

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   export RAILWAY_BACKEND_URL=https://your-backend.railway.app
   export EDITOR_PASSWORD=your_password
   export SECRET_KEY=your_secret_key
   ```

3. **Run Locally**:
   ```bash
   python editor_portal.py
   ```

## 📁 Project Structure

```
├── editor_portal.py          # Main Flask application
├── github_helper.py          # GitHub integration
├── templates/
│   ├── base.html            # Base template
│   ├── index.html           # Dashboard
│   ├── editor.html          # Newsletter editor
│   └── login.html           # Login page
├── static/
│   └── css/
│       └── newsletter.css   # Newsletter styles
├── vercel.json              # Vercel configuration
└── requirements.txt         # Dependencies
```

## 🔄 How It Works

1. **User Interface**: Clean Bootstrap-based interface for managing newsletters
2. **Backend Communication**: Calls Railway backend for newsletter generation
3. **Newsletter Management**: Edit, review, and send newsletters
4. **Email Integration**: Send newsletters via Mailchimp
5. **Version Control**: Save newsletters to GitHub

## 🎨 UI Features

- **Dashboard**: Overview of all newsletters
- **Generation Interface**: One-click newsletter generation
- **Editor**: Rich text editor for newsletter modification
- **Preview**: Live preview of newsletter content
- **Send Interface**: Mailchimp integration for sending
- **AI Review**: Get AI feedback on content quality

## 🔒 Security

- Password-protected editor access
- Secure session management
- Environment variable protection
- HTTPS communication with backend

## 📊 API Endpoints

- `GET /` - Main dashboard
- `GET /editor/<id>` - Newsletter editor
- `POST /api/generate-newsletter` - Generate newsletter
- `POST /api/newsletter/<id>` - Save newsletter
- `POST /api/newsletter/<id>/send` - Send newsletter
- `POST /api/newsletter/<id>/review` - AI review

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
