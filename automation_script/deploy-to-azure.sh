#!/bin/bash
# Quick deployment script for Azure

set -e

echo "🚀 Azure Deployment Script"
echo "=========================="
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Install it first:"
    echo "   brew install azure-cli"
    exit 1
fi

# Variables (customize these)
RESOURCE_GROUP="enquiry-rg"
APP_NAME="enquiry-pdf-processor-$(date +%s)"  # Unique name with timestamp
LOCATION="eastus"
APP_PLAN="enquiry-plan"

echo "📝 Configuration:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   App Name: $APP_NAME"
echo "   Location: $LOCATION"
echo ""

# Login check
echo "🔐 Checking Azure login..."
if ! az account show &> /dev/null; then
    echo "Please login to Azure:"
    az login
fi

echo "✅ Logged in to Azure"
echo ""

# Create resource group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION --output none
echo "✅ Resource group created"
echo ""

# Create App Service plan
echo "🏗️  Creating App Service plan..."
if ! az appservice plan show --name $APP_PLAN --resource-group $RESOURCE_GROUP &> /dev/null; then
    az appservice plan create \
      --name $APP_PLAN \
      --resource-group $RESOURCE_GROUP \
      --sku F1 \
      --is-linux \
      --output none
    echo "✅ App Service plan created (Free tier)"
else
    echo "✅ App Service plan already exists"
fi
echo ""

# Create Web App
echo "🌐 Creating Web App..."
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_PLAN \
  --name $APP_NAME \
  --runtime "PYTHON:3.11" \
  --output none
echo "✅ Web App created"
echo ""

# Get API key
echo "🔑 Please enter your Anthropic API key:"
read -s ANTHROPIC_API_KEY
echo ""

# Configure app settings
echo "⚙️  Configuring app settings..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    CLAUDE_MODEL="claude-sonnet-4-20250514" \
    PORT="8080" \
    WATCH_DIRECTORY="/home/data" \
  --output none
echo "✅ App settings configured"
echo ""

# Configure startup
echo "🚀 Setting startup command..."
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --startup-file "startup.sh" \
  --output none
echo "✅ Startup command set"
echo ""

# Deploy code
echo "📤 Deploying application..."
cd "$(dirname "$0")"
az webapp up \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --runtime "PYTHON:3.11" \
  --output none
echo "✅ Application deployed"
echo ""

# Get URL
URL=$(az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query defaultHostName -o tsv)

echo "=========================="
echo "✅ Deployment Complete!"
echo "=========================="
echo ""
echo "🌐 Your app is live at:"
echo "   https://$URL"
echo ""
echo "📊 View logs:"
echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "🔄 To update the app later:"
echo "   cd $(pwd)"
echo "   az webapp up --resource-group $RESOURCE_GROUP --name $APP_NAME"
echo ""
