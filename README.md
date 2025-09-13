# 🍳 SmartRecipes - AI-Powered Recipe Discovery Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![API](https://img.shields.io/badge/API-Spoonacular-orange.svg)](https://spoonacular.com)

A modern, responsive web application that leverages AI to help users discover personalized recipes based on available ingredients and dietary preferences. Built with Flask and integrated with the Spoonacular API for comprehensive recipe data and nutritional information.

## ✨ Key Features

### 🔍 **Smart Recipe Discovery**
- **Ingredient-based search**: Find recipes using ingredients you already have
- **AI-powered matching**: Advanced algorithm matches ingredients to optimal recipes
- **Dietary filtering**: Support for vegetarian, vegan, gluten-free, keto, paleo, and more
- **Real-time search**: Instant recipe suggestions with pagination support

### 📊 **Comprehensive Recipe Information**
- **Detailed nutrition data**: Calories, protein, carbs, and macro breakdowns
- **Cooking instructions**: Step-by-step recipe directions
- **Ingredient analysis**: Shows what you have vs. what you need
- **Dietary tags**: Clear indicators for dietary restrictions and preferences
- **Cooking time & servings**: Practical information for meal planning

### 🎨 **Modern User Experience**
- **Responsive design**: Optimized for desktop, tablet, and mobile devices
- **Glass morphism UI**: Modern, elegant interface with smooth animations
- **Interactive elements**: Hover effects, loading states, and micro-interactions
- **Search history**: Quick access to previous searches
- **Print-friendly**: Recipe cards optimized for printing

### 🛡️ **Production-Ready Features**
- **Rate limiting**: Prevents API abuse with configurable limits
- **Caching system**: Redis-compatible caching for improved performance
- **Error handling**: Comprehensive error pages and user feedback
- **Security headers**: XSS protection, CSRF prevention, and secure cookies
- **Logging system**: Structured logging with rotation for production monitoring

## 🏗️ Technical Architecture

### **Backend Stack**
- **Framework**: Flask 2.3.3 with Jinja2 templating
- **API Integration**: Spoonacular Recipe API for recipe data
- **Caching**: Flask-Caching with memory storage
- **Rate Limiting**: Flask-Limiter for API protection
- **Environment**: Python-dotenv for configuration management

### **Frontend Technologies**
- **Styling**: Tailwind CSS with custom design system
- **Icons**: Font Awesome 6.5.0 for comprehensive iconography
- **Typography**: Google Fonts (Inter, Poppins) for modern typography
- **Animations**: CSS3 animations with reduced motion support
- **Responsive**: Mobile-first design with breakpoint optimization

### **Security & Performance**
- **Session Management**: Secure session configuration with HTTP-only cookies
- **Input Validation**: Server-side validation for all user inputs
- **API Security**: Request timeout handling and error management
- **Performance**: Lazy loading, image optimization, and efficient caching
- **Accessibility**: WCAG-compliant design with keyboard navigation support

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Spoonacular API key ([Get one here](https://spoonacular.com/food-api))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/smartrecipes.git
   cd smartrecipes
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Create .env file
   echo "SECRET_KEY=your_random_secret_key_here" > .env
   echo "SPOONACULAR_API_KEY=your_spoonacular_api_key" >> .env
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:5000`

## 📁 Project Structure

```
smartrecipes/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (create this)
├── README.md             # Project documentation
├── static/               # Static assets
│   └── images/          # Background images and assets
└── templates/           # Jinja2 templates
    ├── layout.html      # Base template with navigation
    ├── home.html        # Landing page
    ├── input.html       # Recipe search form
    ├── result.html      # Recipe results display
    ├── recipe_detail.html # Individual recipe details
    └── errors/          # Error page templates
        ├── 404.html
        ├── 429.html
        └── 500.html
```

## 🔧 API Integration

### Spoonacular API Features
- **Recipe Search**: Find recipes by ingredients with advanced filtering
- **Recipe Details**: Comprehensive recipe information including nutrition
- **Instructions**: Step-by-step cooking directions
- **Dietary Information**: Automatic detection of dietary restrictions
- **Image Assets**: High-quality recipe images

### Rate Limiting & Caching
- **API Protection**: 10 requests per minute per user
- **Smart Caching**: 30-minute cache for recipe searches, 1-hour for details
- **Error Handling**: Graceful degradation when API limits are exceeded

## 🎯 Core Functionality

### Recipe Search Flow
1. **User Input**: Enter ingredients and select dietary preferences
2. **API Request**: Query Spoonacular API with user parameters
3. **Data Processing**: Extract and format recipe information
4. **Nutrition Analysis**: Calculate and display nutritional data
5. **Results Display**: Present recipes in an interactive grid layout

### Key Algorithms
- **Ingredient Matching**: Smart parsing of comma-separated ingredients
- **Dietary Filtering**: Multi-criteria filtering for dietary restrictions
- **Nutrition Calculation**: Real-time macro and calorie calculations
- **Search Optimization**: Efficient API calls with pagination support

## 🛠️ Development Features

### Code Quality
- **Modular Design**: Clean separation of concerns
- **Error Handling**: Comprehensive try-catch blocks with logging
- **Type Hints**: Python type annotations for better code clarity
- **Documentation**: Inline comments and docstrings

### Performance Optimizations
- **Lazy Loading**: Images load only when needed
- **Caching Strategy**: Multi-level caching for optimal performance
- **Database-free**: Session-based storage for simplicity
- **CDN Ready**: Static assets optimized for CDN deployment

## 🌐 Deployment Considerations

### Production Requirements
- **Environment Variables**: Secure configuration management
- **Logging**: Rotating file handlers for production logs
- **Security**: HTTPS enforcement and secure cookie settings
- **Monitoring**: Health checks and error tracking

### Scalability Features
- **Stateless Design**: No server-side session storage
- **API Rate Limiting**: Prevents abuse and ensures fair usage
- **Caching Layer**: Reduces API calls and improves response times
- **Error Recovery**: Graceful handling of API failures

## 📊 Technical Highlights

### **Backend Architecture**
- RESTful API design with proper HTTP status codes
- Middleware for security headers and request logging
- Modular route organization with clear separation of concerns
- Comprehensive error handling with user-friendly messages

### **Frontend Engineering**
- Mobile-first responsive design
- Progressive enhancement with graceful degradation
- Accessibility features including keyboard navigation
- Performance optimizations with lazy loading and efficient animations

### **Integration Patterns**
- External API integration with proper error handling
- Caching strategies for improved performance
- Rate limiting for API protection
- Session management for user state

## 🔮 Future Enhancements

- **User Authentication**: User accounts and personalized favorites
- **Recipe Collections**: Save and organize favorite recipes
- **Meal Planning**: Weekly meal planning with shopping lists
- **Nutritional Goals**: Track daily nutritional intake
- **Social Features**: Share recipes and cooking experiences
- **Mobile App**: Native mobile application development

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📞 Contact

For questions about this project or to discuss potential opportunities, please reach out through the contact information in your profile.

---

**Built with ❤️ for food lovers and cooking enthusiasts everywhere!**