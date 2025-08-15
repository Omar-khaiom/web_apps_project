# 🍳 SmartRecipes Web Application

A sophisticated Flask web application that helps users discover recipes based on available ingredients, featuring user authentication, favorites system, and nutritional information.

## ✨ Features

- **🔍 Recipe Discovery**: Find recipes based on available ingredients using Spoonacular API
- **👤 User Authentication**: Secure registration with email verification and login system
- **⭐ Favorites System**: Save and manage favorite recipes
- **🥗 Nutritional Info**: View calories, protein, and carbohydrates for recipes
- **🏷️ Dietary Filters**: Support for vegetarian, vegan, gluten-free, and dairy-free options
- **🔒 Security Features**: Rate limiting, CSRF protection, and secure sessions
- **📝 Search History**: Track recent ingredient searches
- **📱 Responsive Design**: Mobile-friendly interface

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with proper migrations
- **Frontend**: HTML, CSS, JavaScript with Bootstrap
- **Email**: Flask-Mail with SMTP integration
- **API**: Spoonacular Recipe API
- **Caching**: Flask-Caching for improved performance
- **Security**: Rate limiting, password hashing, session management

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Spoonacular API key (free tier available)
- Email account with app password for SMTP

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd web_apps_project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\\Scripts\\activate
   # Unix/MacOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

5. **Configure your .env file**
   ```env
   SECRET_KEY=your-super-secret-key-here
   SPOONACULAR_API_KEY=your-spoonacular-api-key
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-specific-password
   ```

6. **Initialize the database**
   ```bash
   python app.py
   # Database tables will be created automatically
   ```

## 🚀 Running the Application

### Development Mode
```bash
python app.py
```
Visit `http://localhost:5000` in your browser.

### Production Deployment
```bash
# Use a proper WSGI server like Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 📊 Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username (3-20 chars)
- `password`: Hashed password
- `email`: Unique email address
- `created_at`: Registration timestamp

### Saved Recipes Table
- `id`: Primary key
- `username`: Foreign key to users
- `recipe_id`: Spoonacular recipe ID
- `recipe_title`: Recipe name
- `recipe_image`: Recipe image URL
- `saved_at`: Timestamp when saved

## 🔧 API Integration

This app integrates with the [Spoonacular API](https://spoonacular.com/food-api) for:
- Recipe search by ingredients
- Detailed recipe information
- Nutritional data
- Cooking instructions

## 🛡️ Security Features

- **Password Security**: Werkzeug password hashing
- **Session Security**: HTTP-only cookies, CSRF protection
- **Rate Limiting**: Prevents abuse of endpoints
- **Input Validation**: Sanitized user inputs
- **Email Verification**: Confirms user email addresses
- **Error Handling**: Comprehensive error pages

## 📁 Project Structure

```
web_apps_project/
├── app.py              # Main Flask application
├── pwa_helpers.py      # PWA and offline functionality
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (not in repo)
├── .env.example       # Environment template
├── .gitignore         # Git ignore rules
├── README.md          # This file
├── logs/              # Application logs
├── templates/         # Jinja2 templates
│   ├── layout.html    # Base template
│   ├── home.html      # Homepage
│   ├── input.html     # Ingredient input
│   ├── result.html    # Recipe results
│   ├── login.html     # Login form
│   ├── register.html  # Registration form
│   ├── favorites.html # User favorites
│   └── errors/        # Error pages
└── static/           # CSS, JS, images
    └── style.css     # Main stylesheet
```

## 🚦 Usage

1. **Home Page**: Welcome page with navigation
2. **Register**: Create account with email verification
3. **Login**: Access your personal account
4. **Recipe Search**: Enter ingredients to find recipes
5. **Recipe Details**: View full recipe information
6. **Favorites**: Save and manage favorite recipes

## 🔄 Features in Development

- [ ] Recipe meal planning
- [ ] Shopping list generation  
- [ ] Social recipe sharing
- [ ] Advanced search filters
- [ ] Recipe rating system

## 🐛 Known Issues

- Pending registrations stored in memory (use Redis for production)
- Limited error recovery for API failures
- No automated testing suite

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Spoonacular API](https://spoonacular.com/) for recipe data
- [Flask](https://flask.palletsprojects.com/) web framework
- [Bootstrap](https://getbootstrap.com/) for responsive design

## 📞 Support

For issues or questions:
1. Check the GitHub issues page
2. Create a new issue with detailed description
3. Include error logs and steps to reproduce

---

**Built with ❤️ by [SmartRecipes ]**
