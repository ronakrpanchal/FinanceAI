# FinanceAI Backend

This is the backend service for the FinanceAI application, providing AI-powered financial management features including receipt parsing, budget generation, and personalized financial recommendations.

## Features

- **Receipt Parsing**: Extract and categorize expenses from receipt images
- **Budget Generation**: Create personalized budgets based on user descriptions
- **Financial Recommendations**: Get AI-powered financial advice based on spending patterns

## Project Structure

```
AI-backend/
├── main.py              # Flask application and API endpoints
├── reciept.py           # Receipt parsing and processing
├── budget.py            # Budget generation and management
├── recommender.py       # Financial recommendations engine
├── db.py                # Database operations
└── finance_ai.db        # SQLite database
```

## API Endpoints

### 1. Parse Receipt
- **Endpoint**: `/parse-receipt`
- **Method**: POST
- **Description**: Processes receipt images and extracts transaction details
- **Request Body**:
  ```json
  {
    "image_url": "string",
    "user_id": "string"
  }
  ```

### 2. Generate Budget
- **Endpoint**: `/generate-budget`
- **Method**: POST
- **Description**: Creates a budget based on user description
- **Request Body**:
  ```json
  {
    "user_id": "string",
    "description": "string"
  }
  ```

### 3. Get Recommendations
- **Endpoint**: `/get-recommendations`
- **Method**: POST
- **Description**: Generates personalized financial recommendations
- **Request Body**:
  ```json
  {
    "user_id": "string"
  }
  ```

## Environment Variables

Create a `.env` file with the following variables:
```
GROQ_API_KEY=your_groq_api_key
MODEL_NAME=your_preferred_model_name
```

## Setup and Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Database Schema

The application uses SQLite (`finance_ai.db`) to store:
- User transactions
- Budget information
- Receipt data
- Financial recommendations

## Dependencies

- Flask
- pandas
- langchain-groq
- python-dotenv
- SQLite3

## Error Handling

All endpoints include proper error handling and return appropriate HTTP status codes:
- 200: Success
- 400: Bad Request
- 500: Internal Server Error

## Security

- API endpoints require user authentication
- Environment variables are used for sensitive information
- Input validation is performed on all endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 