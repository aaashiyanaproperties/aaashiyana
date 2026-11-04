import { initializeApp, getApps, type FirebaseApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, type Auth } from 'firebase/auth';
const config={apiKey:process.env.NEXT_PUBLIC_FIREBASE_API_KEY,authDomain:process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,projectId:process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,appId:process.env.NEXT_PUBLIC_FIREBASE_APP_ID};
export const firebaseReady=Boolean(config.apiKey&&config.authDomain&&config.projectId&&config.appId);
let app:FirebaseApp|undefined;
if(firebaseReady) app=getApps()[0]??initializeApp(config);
export const firebaseAuth:Auth|null=app?getAuth(app):null;
export const googleProvider=firebaseReady?new GoogleAuthProvider():null;
