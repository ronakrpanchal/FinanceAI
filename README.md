# FinanceAI - AI-Powered Financial Management System

FinanceAI is an intelligent financial management system that processes receipts, manages budgets, and provides personalized financial recommendations using advanced AI techniques.

## 🌟 Features

- **Receipt Processing**: Automatically extract and categorize items from receipt images
- **Budget Management**: Create and update budgets through natural language
- **Financial Recommendations**: Get personalized financial insights based on your spending patterns
- **Subscription Tracking**: Manage and track recurring subscriptions
- **Debt Management**: Monitor loans and debts with interest rates
- **MongoDB Integration**: Securely store and analyze your financial data

## 🏗️ Architecture

The system consists of two main components:

### 1. AI Backend
- **Receipt Parser** (`reciept.py`): Processes receipt images using computer vision (OpenCV) and OCR (pytesseract), then extracts structured data using LLM (Groq)
- **Budget Manager** (`budget.py`): Handles budget creation and updates through natural language processing
- **Financial Recommender** (`recommender.py`): Analyzes spending patterns and provides personalized financial advice
- **API Server** (`main.py`): Flask server that exposes endpoints for the frontend

### 2. Streamlit Frontend
- **Home Dashboard** (`home.py`): Main dashboard for transaction management and receipt uploads
- **Budget Planning** (`budgets.py`): Budget setup, tracking, and AI-assisted budget generation
- **Subscription Manager** (`subscriptions.py`): Track and manage recurring subscriptions
- **Debt Tracker** (`debts.py`): Monitor loans and debts with interest rates

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- MongoDB
- Tesseract OCR
- Groq API access

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/finance-ai.git
   cd finance-ai
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Tesseract OCR:
   - **Linux**: `sudo apt-get install tesseract-ocr`
   - **macOS**: `brew install tesseract`
   - **Windows**: Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

4. Set up environment variables:
   Create a `.env` file in the project root with the following variables:
   ```
   GROQ_API_KEY=your_groq_api_key
   MODEL_NAME=llama3-70b-8192  # or another compatible model
   MONGO_URI=mongodb://localhost:27017/
   ```

5. Start MongoDB:
   ```bash
   mongod --dbpath=/path/to/data/db
   ```

## 🚀 Usage

### Starting the Backend API Server

```bash
# Navigate to the AI-backend directory
cd AI-backend
python main.py
```

The API server will start on `http://localhost:5000` by default.

### Starting the Frontend

```bash
# Navigate to the Frontend directory
cd Frontend
streamlit run app.py
```

The Streamlit interface will be accessible at `http://localhost:8501`.

### User Interface Components

1. **Home Dashboard**: 
   - Add new income/expense transactions
   - Upload receipts for automatic parsing
   - View transaction history
   - Request AI-powered financial recommendations

2. **Budget Planning**:
   - Set income and savings goals
   - Allocate budget amounts across categories
   - Generate budgets through natural language using AI
   - Compare actual spending with budget allocations

3. **Subscription Manager**:
   - Add, edit, and cancel subscriptions
   - Track monthly subscription costs
   - Prioritize subscriptions based on usage and importance

4. **Debt Tracker**:
   - Monitor loans and debts
   - Track principal amounts and interest rates
   - Prioritize debts for optimal repayment strategy

### API Endpoints

1. **Parse Receipt**
   ```
   POST /parse-receipt
   
   {
     "image_url": "base64_encoded_image_or_url",
     "user_id": "user_id",
     "category": "groceries"
   }
   ```

2. **Generate/Update Budget**
   ```
   POST /generate-budget
   
   {
     "user_id": "user_id",
     "description": "Set my monthly income to $5000 and allocate $1500 for rent"
   }
   ```

3. **Get Financial Recommendations**
   ```
   POST /get-recommendations
   
   {
     "user_id": "user_id"
   }
   ```

## 📊 Data Structure

### MongoDB Collections

1. **transactions**:
   - user_id: String
   - transaction_date: String
   - amount: Float
   - amount_type: "debit" | "credit"
   - category: String
   - description: String

2. **budgets**:
   - user_id: String
   - budget_data: Object
     - income: Float
     - savings: Float
     - expenses: Array[{category: String, allocated_amount: Float}]

3. **subscriptions**:
   - user_id: String
   - name: String
   - cost: Float
   - usage: String ("Daily" | "Weekly" | "Monthly" | "Occasionally")
   - priority: String ("High" | "Medium" | "Low")
   - created_at: DateTime

4. **debts**:
   - user_id: String
   - name: String
   - amount: Float
   - interest_rate: Float
   - priority: String ("High" | "Medium" | "Low")
   - created_at: DateTime

## 🧠 AI Components

### Receipt Processing Pipeline

1. Image preprocessing with multiple approaches (adaptive thresholding, Otsu's method, etc.)
2. OCR text extraction using Tesseract
3. Structured data extraction using Groq LLM
4. Fallback mechanisms for better reliability

### Budget Processing

Natural language budget instructions are processed by a Groq LLM and structured into a JSON format. The system intelligently merges new budget information with existing data.

### Financial Recommendations

The system:
1. Analyzes transaction patterns and budget adherence
2. Evaluates debt, savings, and subscription risks
3. Provides actionable financial advice and identifies areas for improvement

## 🧩 Key Features Implementation

### Automatic Subscription Management
- Subscriptions are automatically added as transactions at the beginning of each month
- System tracks usage patterns and suggests optimizations

### AI-Powered Budget Generation
- Natural language processing allows users to describe their budget goals
- System automatically allocates funds across categories based on user input

### Visual Receipt Scanning
- Computer vision techniques extract text from receipt images
- AI processing identifies items, prices, and store information
- Transactions are automatically categorized and stored

### Interactive Financial Recommendations
- AI analyzes spending patterns, debt levels, and budget adherence
- Personalized recommendations are presented with animated typing effect
- Risk assessments provided for debt, savings, and subscription spending

## 📱 Frontend Implementation Details

The frontend is built using Streamlit, a Python library for creating web applications with minimal code:

### Home Dashboard (`home.py`)
- Transaction management interface
- Receipt upload and processing
- AI recommendations with animated typing effect
- Transaction history with color-coded display

### Budget Planning (`budgets.py`)
- AI-assisted budget generation through natural language
- Manual budget configuration for income, savings, and category allocations
- Budget vs. actual expense comparison
- Category mapping for accurate expense tracking

### Subscription Manager (`subscriptions.py`)
- Add, edit, and cancel subscription services
- Track monthly costs and usage frequency
- Prioritization system for subscription value assessment

### Debt Tracker (`debts.py`)
- Record and monitor loans and debts
- Track interest rates and principal amounts
- Prioritization system for optimal debt management

## 🔒 Security Notes

- Ensure your MongoDB instance is properly secured
- Keep your `.env` file private and never commit it to version control
- Consider implementing user authentication for API endpoints
- Implement secure handling of receipt images

## 🔧 Troubleshooting

- **OCR Issues**: If receipt parsing is inaccurate, try improving image quality or lighting
- **MongoDB Connection**: Verify your connection string and ensure MongoDB is running
- **API Key Errors**: Check that your Groq API key is valid and has sufficient permissions
- **Frontend-Backend Connection**: Ensure the Flask API is running before starting Streamlit

## 📝 License

[MIT License](LICENSE)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.