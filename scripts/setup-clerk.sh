#!/usr/bin/env bash
# Setup Clerk authentication keys and link admin user
# Run this after creating a Clerk application at https://clerk.com
#
# Usage: bash scripts/setup-clerk.sh <publishable_key> <secret_key> <clerk_user_id>
# Example: bash scripts/setup-clerk.sh pk_test_abc123 sk_test_xyz789 user_2abc123

set -e

export PATH="/c/Users/LoganKirby/.local/pgsql/pgsql/bin:$PATH"

PUBLISHABLE_KEY="${1:?Usage: $0 <publishable_key> <secret_key> <clerk_user_id>}"
SECRET_KEY="${2:?Usage: $0 <publishable_key> <secret_key> <clerk_user_id>}"
CLERK_USER_ID="${3:?Usage: $0 <publishable_key> <secret_key> <clerk_user_id>}"

PROJECT_DIR="/c/Users/LoganKirby/hotel-asset-management"

echo "=== Setting up Clerk credentials ==="

# Update backend .env
echo "Updating backend/.env ..."
sed -i "s|^CLERK_SECRET_KEY=.*|CLERK_SECRET_KEY=$SECRET_KEY|" "$PROJECT_DIR/backend/.env"
sed -i "s|^CLERK_PUBLISHABLE_KEY=.*|CLERK_PUBLISHABLE_KEY=$PUBLISHABLE_KEY|" "$PROJECT_DIR/backend/.env"

# Create frontend .env.local
echo "Creating frontend/.env.local ..."
cat > "$PROJECT_DIR/frontend/.env.local" <<EOF
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$PUBLISHABLE_KEY
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
EOF

# Link admin user's clerk_id in the database
echo "Linking admin user to Clerk ID: $CLERK_USER_ID ..."
psql -U postgres -d hotel_am -c "
UPDATE users
SET clerk_id = '$CLERK_USER_ID'
WHERE email = 'admin@missionhill.com';
"

echo ""
echo "=== Clerk setup complete ==="
echo "  Backend .env updated with CLERK_SECRET_KEY and CLERK_PUBLISHABLE_KEY"
echo "  Frontend .env.local created with NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
echo "  Admin user linked to Clerk ID: $CLERK_USER_ID"
echo ""
echo "Restart the backend and frontend to apply changes."
