#!/bin/bash
# Azure Container deployment script

set -e

echo "🐳 Azure Container Deployment"
echo "=============================="
echo ""

# Variables
RESOURCE_GROUP="enquiry-rg"
LOCATION="eastus"
ACR_NAME="enquiryacr$(date +%s)"
CONTAINER_NAME="enquiry-app"
IMAGE_NAME="enquiry-pdf-processor"
DNS_LABEL="enquiry-$(date +%s)"

echo "📝 Configuration:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Container Registry: $ACR_NAME"
echo "   Container Name: $CONTAINER_NAME"
echo "   Location: $LOCATION"
echo ""

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Install: brew install azure-cli"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install: brew install docker"
    exit 1
fi

# Login
echo "🔐 Checking Azure login..."
if ! az account show &> /dev/null; then
    az login
fi
echo "✅ Logged in"
echo ""

# Load API key from .env file
echo "🔑 Loading Anthropic API key from .env..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    exit 1
fi

# Source the .env file to get the API key
export $(grep -v '^#' .env | xargs)

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY not found in .env file"
    exit 1
fi
echo "✅ API key loaded"
echo ""

# Create resource group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION --output none
echo "✅ Resource group ready"
echo ""

# Create Azure Container Registry
echo "🏗️  Creating Azure Container Registry..."
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true \
  --output none
echo "✅ Container registry created"
echo ""

# Get ACR credentials
echo "🔑 Getting registry credentials..."
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
echo "✅ Credentials retrieved"
echo ""

# Build and push Docker image
echo "🐳 Building Docker image..."
cd "$(dirname "$0")"
docker build -t $IMAGE_NAME:latest .
echo "✅ Image built"
echo ""

echo "📤 Tagging and pushing to ACR..."
docker tag $IMAGE_NAME:latest $ACR_LOGIN_SERVER/$IMAGE_NAME:latest
az acr login --name $ACR_NAME
docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:latest
echo "✅ Image pushed"
echo ""

# Deploy to Azure Container Instances
echo "🚀 Deploying container..."
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image $ACR_LOGIN_SERVER/$IMAGE_NAME:latest \
  --registry-login-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label $DNS_LABEL \
  --ports 8080 \
  --cpu 1 \
  --memory 2 \
  --environment-variables \
    ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    CLAUDE_MODEL="claude-sonnet-4-20250514" \
    PORT="8080" \
  --output none

echo "✅ Container deployed"
echo ""

# Get container URL
FQDN=$(az container show \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --query ipAddress.fqdn -o tsv)

echo "=============================="
echo "✅ Deployment Complete!"
echo "=============================="
echo ""
echo "🌐 Your app is live at:"
echo "   http://$FQDN:8080"
echo ""
echo "📊 View container logs:"
echo "   az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
echo ""
echo "🔄 To update:"
echo "   docker build -t $IMAGE_NAME:latest ."
echo "   docker tag $IMAGE_NAME:latest $ACR_LOGIN_SERVER/$IMAGE_NAME:latest"
echo "   docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:latest"
echo "   az container restart --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
echo ""
echo "🗑️  To delete everything:"
echo "   az group delete --name $RESOURCE_GROUP --yes"
echo ""
