# Blockchain Wallet Management System

A transaction-focused blockchain wallet management system

## Key Features

- Transaction-based balance management (no direct balance field)
- Secure private key encryption
- Complete transaction history with status management
- Transaction rollback mechanism
- Comprehensive API for wallet management
- Race condition prevention
- Tests covering core functionality

## Future Improvements

- Using intermediate tables for storing each Account's transactions (Providing faster balance calculation and transaction history report)
- Implement caching for balance calculations

## Project Setup

1. Configure environment variables
Create a **.env** file based on *.env.example* in the same place where it is located and update its variables based on your environment and project setup.

2. Generate an encryption key
    - \$ ```chmod +x generate_key.sh```
    - \$ ```./generate_key.sh```

3. Create and activate a virtual environment
    - \$ ```python3 -m vevn venv```
    - \$ ```source ./venv/bin/activate``` (For Linux)
4. Install project requirements
    - \$ ```pip install -r requirements.txt```

## How to Run

### Running migrations
\$ ```python manage.py makemigrations```
\$ ```python manage.py migrate```

### Running development server
\$ ```python manage.py runserver```

## Running Tests

\$ ```pytest .```

## API Usage Examples

### Create a new account

```bash
curl -X POST http://localhost:8000/accounts/ \
  -H "Content-Type: application/json" \
  -d '{"public_address": "0x1234567890abcdef"}'
```

### Make a deposit

```bash
curl -X POST http://localhost:8000/transactions/deposit/ \
  -H "Content-Type: application/json" \
  -d '{"account": "account-uuid-here", "amount": "100.5"}'
```

### Make a withdrawal

```bash
curl -X POST http://localhost:8000/transactions/withdraw/ \
  -H "Content-Type: application/json" \
  -d '{"account": "account-uuid-here", "amount": "50.25"}'
```

### Check balance

```bash
curl http://localhost:8000/accounts/account-uuid-here/balance/
```

### Get transaction history

```bash
curl http://localhost:8000/accounts/account-uuid-here/transactions/
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/accounts/` | POST | Create a new account |
| `/accounts/{id}/` | GET | Retrieve account details |
| `/accounts/{id}/balance/` | GET | Get account balance |
| `/accounts/{id}/transactions/` | GET | Get account transaction history |
| `/transactions/` | GET | List all transactions |
| `/transactions/{id}/` | GET | Retrieve transaction details |
| `/transactions/deposit/` | POST | Make a deposit |
| `/transactions/withdraw/` | POST | Make a withdrawal |

## Technical Implementation Details

### Balance Calculation

The system doesn't store balance directly. Instead, it calculates it on-the-fly by summing all completed transactions:
- Deposits add to the balance
- Withdrawals subtract from the balance
- Only COMPLETED transactions affect balance
- Performance optimized using database aggregation

### Transaction States

Transactions follow a state machine:
- PENDING: Initial state when created
- COMPLETED: Successfully processed
- FAILED: Transaction that failed to process

### Security Features

- Private keys encrypted using Fernet symmetric encryption
- Database transaction isolation to prevent race conditions
- Input validation to prevent invalid transactions
- Balance verification before withdrawal

## Performance Considerations

- Transaction querying optimized with database indexes
- Balance calculation uses SQL-level aggregation
- Atomic transactions prevent data corruption
- Proper exception handling