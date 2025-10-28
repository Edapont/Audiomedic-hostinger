#!/bin/bash

# First login as admin to get token
echo "1. Login as admin..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"candidodapont@gmail.com","password":"Test1234!"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" = "null" ]; then
    echo "❌ Login failed"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Token obtained"
echo ""

# Try to renew subscription for test user
echo "2. Attempting to renew subscription for testuser@test.com..."
RENEW_RESPONSE=$(curl -s -X PUT http://localhost:8001/api/admin/users/e7c0b2b9-d633-4a03-8a00-772bcd7d1524/subscription \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"months":1}')

echo "Response:"
echo $RENEW_RESPONSE | jq

