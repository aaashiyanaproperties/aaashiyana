# Firebase Authentication setup

1. Open Firebase Console and select project `aashiyana`.
2. Add a Web App and copy its web config into `.env.local` as `NEXT_PUBLIC_FIREBASE_API_KEY`, `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`, `NEXT_PUBLIC_FIREBASE_PROJECT_ID`, and `NEXT_PUBLIC_FIREBASE_APP_ID`.
3. In Authentication → Sign-in method, enable Google and Phone.
4. Add `localhost` and your deployed frontend domain to Authentication → Settings → Authorized domains.
5. For Phone OTP, configure billing/quotas as Firebase requires and use Firebase fictional phone numbers for development tests.
6. In Project settings → Service accounts, generate a private key. Store the complete JSON securely in the backend secret manager as `FIREBASE_SERVICE_ACCOUNT_JSON` (single-line JSON string). Never put this JSON in a `NEXT_PUBLIC_` variable or source control.
7. Set `FIREBASE_PROJECT_ID=aashiyana`, `DEV_AUTH_BYPASS=false`, and deploy/restart the API.

The frontend uses Firebase Google popup and phone OTP with an invisible reCAPTCHA verifier. The API verifies Firebase ID tokens and creates the corresponding PostgreSQL user on first authenticated request. Role assignment is server-side only; choosing a role in the local demo UI does not grant production privileges.
