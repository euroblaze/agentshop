# AgentShop - AI Agent Software Marketplace

A comprehensive e-commerce platform for AI agent software with a modern React frontend and Flask backend. Built with security, performance, and developer experience in mind.

## 🚀 Features

### Core E-commerce Features
- **Product Management**: Browse AI agent software with categories, search, and filtering
- **Shopping Cart**: Add products to cart with session persistence
- **Order Processing**: Complete checkout flow with order history
- **User Authentication**: Customer registration, login, and profile management
- **Payment Integration**: Ready for payment gateway integration (Stripe, PayPal)

### Security Features
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Input Validation**: Comprehensive sanitization and validation
- **Rate Limiting**: Protection against DDoS and brute force attacks
- **SQL Injection Protection**: Parameterized queries and validation
- **XSS Protection**: Content Security Policy and input sanitization
- **Password Security**: Strong hashing with bcrypt and complexity requirements

### Technical Features
- **RESTful API**: Complete REST API with proper HTTP methods
- **Database Migrations**: Alembic for database version control
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Type Safety**: Full TypeScript implementation
- **Error Handling**: Comprehensive error handling and logging

## 🛠️ Tech Stack

### Backend
- **Framework**: Flask 2.3+
- **Database**: SQLAlchemy ORM with SQLite (configurable for PostgreSQL/MySQL)
- **Authentication**: Flask-JWT-Extended
- **Security**: Redis for rate limiting, bcrypt for passwords
- **API**: RESTful endpoints with JSON responses

### Frontend
- **Framework**: React 18 with TypeScript
- **Routing**: React Router v6
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Build Tool**: Vite

## 📁 Project Structure

```
agentshop/
├── backend/
│   ├── controllers/          # API endpoint controllers
│   ├── services/            # Business logic services
│   ├── models/              # Database models
│   ├── utils/               # Utilities (serializers, etc.)
│   ├── security/            # Security modules
│   ├── middleware/          # Flask middleware
│   ├── migrations/          # Database migrations
│   └── app.py              # Flask application entry point
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Page components
│   │   ├── models/         # TypeScript models
│   │   ├── services/       # API services
│   │   ├── security/       # Frontend security
│   │   └── App.tsx         # Main React component
│   └── package.json
└── README.md
```

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Redis (for security features)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd agentshop
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example .env
# Edit .env with your configuration

# Initialize database
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Run the backend
python app.py
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🔧 Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///agentshop.db
JWT_SECRET_KEY=your-jwt-secret-here

# Redis (for security features)
REDIS_URL=redis://localhost:6379

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Email (optional - using Brevo)
MAIL_SERVER=smtp-relay.brevo.com
MAIL_PORT=587
MAIL_USERNAME=your-brevo-login@example.com
MAIL_PASSWORD=your-brevo-smtp-key
```

## 🛡️ Security Features

### Authentication
- JWT tokens with configurable expiration
- Refresh token mechanism
- Password hashing with bcrypt
- Failed login attempt tracking

### API Security
- Rate limiting per IP and endpoint
- SQL injection protection
- XSS prevention
- CSRF token validation
- Security headers (CSP, HSTS, etc.)

### Data Protection
- Input sanitization and validation
- Sensitive data masking in logs
- Secure session management
- Device fingerprinting

## 📋 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh JWT token

### Products
- `GET /api/products` - List products
- `GET /api/products/{id}` - Get product details
- `GET /api/products/categories` - Get categories
- `GET /api/products/search` - Search products

### Cart
- `GET /api/cart` - Get cart contents
- `POST /api/cart/items` - Add item to cart
- `PUT /api/cart/items/{id}` - Update cart item
- `DELETE /api/cart/items/{id}` - Remove cart item

### Orders
- `GET /api/orders` - Get customer orders
- `POST /api/orders` - Create new order
- `GET /api/orders/{id}` - Get order details
- `POST /api/orders/{id}/cancel` - Cancel order

### Customers
- `GET /api/customers/me` - Get current customer
- `PUT /api/customers/me` - Update customer profile
- `POST /api/customers/change-password` - Change password

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Production Checklist
1. Set strong SECRET_KEY and JWT_SECRET_KEY
2. Use PostgreSQL or MySQL instead of SQLite
3. Set up Redis for rate limiting
4. Configure proper CORS origins
5. Set up SSL/TLS certificates
6. Configure email service
7. Set up monitoring and logging
8. Configure backup strategy

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Known Issues

- LLM endpoints need proper service implementation
- Payment gateway integration needs completion
- Email service requires configuration
- Admin panel needs frontend implementation

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting guide

## 🗺️ Roadmap

- [ ] Payment gateway integration (Stripe/PayPal)
- [ ] Email notification system
- [ ] Admin dashboard frontend
- [ ] File upload/download system
- [ ] Advanced search and filtering
- [ ] Product reviews and ratings
- [ ] Wishlist functionality
- [ ] Multi-language support
