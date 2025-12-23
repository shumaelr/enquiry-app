# Azure Deployment Instructions

## Prerequisites
1. Azure account (create free at https://azure.microsoft.com/free/)
2. Azure CLI installed (`brew install azure-cli` on Mac)

## Deployment Steps

### 1. Login to Azure
```bash
az login
```

### 2. Create Resource Group
```bash
az group create --name enquiry-rg --location eastus
```

### 3. Create App Service Plan (Linux)
```bash
az appservice plan create \
  --name enquiry-plan \
  --resource-group enquiry-rg \
  --sku B1 \
  --is-linux
```

### 4. Create Web App
```bash
az webapp create \
  --resource-group enquiry-rg \
  --plan enquiry-plan \
  --name enquiry-pdf-processor \
  --runtime "PYTHON:3.11"
```

### 5. Configure Environment Variables
```bash
az webapp config appsettings set \
  --resource-group enquiry-rg \
  --name enquiry-pdf-processor \
  --settings \
    ANTHROPIC_API_KEY="your-api-key-here" \
    CLAUDE_MODEL="claude-sonnet-4-20250514" \
    PORT="8080"
```

### 6. Configure Startup Command
```bash
az webapp config set \
  --resource-group enquiry-rg \
  --name enquiry-pdf-processor \
  --startup-file "startup.sh"
```

### 7. Deploy Code
```bash
cd /Users/shumaelr/RealCode/Enquiry/automation_script
az webapp up \
  --resource-group enquiry-rg \
  --name enquiry-pdf-processor \
  --runtime "PYTHON:3.11"
```

### 8. Enable Logging (Optional)
```bash
az webapp log config \
  --resource-group enquiry-rg \
  --name enquiry-pdf-processor \
  --application-logging filesystem \
  --level information
```

### 9. View Logs
```bash
az webapp log tail \
  --resource-group enquiry-rg \
  --name enquiry-pdf-processor
```

## Post-Deployment

Your app will be available at:
**https://enquiry-pdf-processor.azurewebsites.net**

## Updating the App
```bash
cd /Users/shumaelr/RealCode/Enquiry/automation_script
az webapp up \
  --resource-group enquiry-rg \
  --name enquiry-pdf-processor
```

## Storage Configuration

Since Azure App Service uses ephemeral storage, you'll need to:

1. **Option A: Use Azure Blob Storage** (Recommended)
   - Store PDF files and outputs in Azure Blob Storage
   - Modify code to use Azure Storage SDK

2. **Option B: Use Azure Files**
   - Mount Azure Files as persistent storage
   ```bash
   az webapp config storage-account add \
     --resource-group enquiry-rg \
     --name enquiry-pdf-processor \
     --custom-id enquiry-storage \
     --storage-type AzureFiles \
     --share-name enquiry-files \
     --account-name <storage-account-name> \
     --access-key <access-key> \
     --mount-path /home/data
   ```

## Scaling

Upgrade to a larger plan if needed:
```bash
az appservice plan update \
  --name enquiry-plan \
  --resource-group enquiry-rg \
  --sku P1V2
```

## Troubleshooting

1. Check logs: `az webapp log tail --name enquiry-pdf-processor --resource-group enquiry-rg`
2. SSH into container: `az webapp ssh --name enquiry-pdf-processor --resource-group enquiry-rg`
3. Restart app: `az webapp restart --name enquiry-pdf-processor --resource-group enquiry-rg`

## Cost Estimation
- B1 Plan: ~$13/month
- P1V2 Plan: ~$75/month
- Storage: ~$0.02/GB/month
