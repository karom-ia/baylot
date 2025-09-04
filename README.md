## Setup Environment

1. Copy `.env.example` to `.env`
2. Fill in your actual credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `uvicorn app.main:app --reload`

## Environment Variables

- `ADMIN_USERNAME` - Admin username for docs
- `ADMIN_PASSWORD` - Admin password for docs  
- `ADMIN_KEY` - API admin key for ticket operations
- `SECRET_KEY` - Generate with: `openssl rand -hex 32`
- `DATABASE_URL` - PostgreSQL connection string
- `SOLANA_WALLET_ADDRESS` - Your Solana wallet address