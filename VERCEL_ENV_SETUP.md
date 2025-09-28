# Vercel Environment Variables Setup Guide

## 🚨 Important: Environment Variables Must Be Set in Vercel Dashboard

The `vercel.json` file does NOT contain environment variables. You must set them manually in the Vercel dashboard.

## 📋 Step-by-Step Instructions

### 1. Go to Vercel Dashboard
- Visit [vercel.com](https://vercel.com)
- Sign in to your account
- Select your `alphaminr_frontend` project

### 2. Navigate to Environment Variables
- Click on your project
- Go to **Settings** tab
- Click on **Environment Variables** in the left sidebar

### 3. Add Required Variables

Add each of these variables one by one:

#### **RAILWAY_BACKEND_URL** (Required)
- **Name**: `RAILWAY_BACKEND_URL`
- **Value**: `https://your-app.railway.app` (replace with your actual Railway URL)
- **Environment**: Production, Preview, Development

#### **EDITOR_PASSWORD** (Required)
- **Name**: `EDITOR_PASSWORD`
- **Value**: `your_secure_password_here`
- **Environment**: Production, Preview, Development

#### **SECRET_KEY** (Required)
- **Name**: `SECRET_KEY`
- **Value**: `your_random_secret_key_here` (generate a random string)
- **Environment**: Production, Preview, Development

#### **ANTHROPIC_API_KEY** (Optional - for AI review)
- **Name**: `ANTHROPIC_API_KEY`
- **Value**: `your_anthropic_api_key_here`
- **Environment**: Production, Preview, Development

#### **MAILCHIMP_API_KEY** (Optional - for sending newsletters)
- **Name**: `MAILCHIMP_API_KEY`
- **Value**: `your_mailchimp_api_key_here`
- **Environment**: Production, Preview, Development

#### **MAILCHIMP_SERVER_PREFIX** (Optional - for Mailchimp)
- **Name**: `MAILCHIMP_SERVER_PREFIX`
- **Value**: `us1` (or your server prefix)
- **Environment**: Production, Preview, Development

#### **MAILCHIMP_LIST_ID** (Optional - for Mailchimp)
- **Name**: `MAILCHIMP_LIST_ID`
- **Value**: `your_mailchimp_list_id_here`
- **Environment**: Production, Preview, Development

### 4. Redeploy
- After adding all environment variables, trigger a new deployment
- Go to **Deployments** tab
- Click **Redeploy** on the latest deployment

## 🔍 How to Get Your Railway Backend URL

1. Go to [Railway.app](https://railway.app)
2. Sign in and select your `alphaminr_backend` project
3. Go to **Settings** → **Domains**
4. Copy the production domain (e.g., `https://your-app.railway.app`)
5. Use this URL as your `RAILWAY_BACKEND_URL`

## ✅ Verification

After setting up environment variables:

1. **Check Deployment Logs**: Look for any environment variable errors
2. **Test Frontend**: Visit your Vercel URL and try to generate a newsletter
3. **Check Backend Connection**: The frontend should successfully call the Railway backend

## 🚨 Common Issues

- **"RAILWAY_BACKEND_URL references Secret"**: This means you're trying to reference a secret that doesn't exist. Set the environment variable directly in Vercel dashboard instead.
- **"Environment variable not found"**: Make sure you've set the variable for all environments (Production, Preview, Development).
- **Backend connection failed**: Verify your Railway backend URL is correct and the backend is deployed and running.

## 📞 Need Help?

If you're still having issues:
1. Check the Vercel deployment logs
2. Verify all environment variables are set correctly
3. Ensure your Railway backend is deployed and accessible
4. Test the backend URL directly in your browser
