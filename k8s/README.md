# Kubernetes Deployment for Note-RAGS

This directory contains Kubernetes manifests to deploy PostgreSQL database and Notes-API.

## Files Created:
- `namespace.yaml` - Creates 'note-rags' namespace
- `postgres-configmap.yaml` - PostgreSQL configuration
- `postgres-secret.yaml` - PostgreSQL credentials
- `postgres-storage.yaml` - Persistent storage for database
- `postgres-deployment.yaml` - PostgreSQL deployment
- `postgres-service.yaml` - PostgreSQL internal service
- `notes-api-configmap.yaml` - Notes-API configuration  
- `notes-api-secret.yaml` - JWT secrets for Notes-API
- `notes-api-deployment.yaml` - Notes-API deployment
- `notes-api-service.yaml` - Notes-API external service (port 8003)

## Next Steps:

1. **Build the Notes-API image:**
   ```bash
   docker build -f notes-api/Dockerfile -t notes-api:latest .
   ```

2. **Apply all manifests:**
   ```bash
   kubectl apply -f k8s/
   ```

3. **Check deployment status:**
   ```bash
   kubectl get pods -n note-rags
   kubectl get services -n note-rags
   ```

4. **Access your API:**
   - The notes-api will be available at `localhost:8003` (or your cluster's LoadBalancer IP)

## Key Learning Points:
- **Namespace**: Isolates resources
- **ConfigMap**: Non-sensitive configuration
- **Secret**: Sensitive data (base64 encoded)
- **PVC**: Persistent storage claims
- **Deployment**: Manages pod replicas and updates
- **Service**: Network access to pods