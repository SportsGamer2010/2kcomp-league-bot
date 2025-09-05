# Deployment Automation Guide

## 🚀 Overview

The 2KCompLeague Discord Bot includes a comprehensive deployment automation system that handles CI/CD, health monitoring, and automated deployments across multiple environments.

## 🏗️ Architecture

### Components

1. **GitHub Actions Workflow** (`.github/workflows/ci-cd.yml`)
   - Automated testing and security scanning
   - Docker image building and pushing
   - Environment-specific deployments

2. **Deployment Scripts** (`scripts/`)
   - `deploy.sh` - Main deployment automation
   - `health-monitor.sh` - Continuous health monitoring
   - `send-alert.sh` - Alert notification system

3. **Configuration Files**
   - `deployment-config.yml` - Environment-specific settings
   - `docker-compose.yml` - Development/staging configuration
   - `docker-compose.prod.yml` - Production configuration

4. **Makefile Integration**
   - Automated deployment commands
   - Health monitoring commands
   - CI/CD integration commands

## 🎯 Quick Start

### 1. Automated Deployment

```bash
# Deploy to production with backup
make deploy-auto

# Deploy to staging
make deploy-staging

# Manual deployment
make deploy
```

### 2. Health Monitoring

```bash
# Start continuous monitoring
make health-monitor

# Run single health check
make health-check

# View health status
make status
```

### 3. CI/CD Pipeline

```bash
# Run CI test suite
make ci-test

# Run security scans
make ci-security

# Full quality check
make quality
```

## 🔧 Configuration

### Environment Variables

```bash
# Discord Bot Configuration
DISCORD_TOKEN=your_bot_token
GUILD_ID=your_guild_id
ANNOUNCE_CHANNEL_ID=channel_id
HISTORY_CHANNEL_ID=channel_id

# Deployment Configuration
DISCORD_WEBHOOK_URL=webhook_url_for_alerts
EMAIL_RECIPIENT=admin@example.com

# API Configuration
SPORTSPRESS_BASE=https://2kcompleague.com/wp-json/sportspress/v2
SPORTSPRESS_API_KEY=your_api_key
```

### Deployment Configuration

The `deployment-config.yml` file defines settings for each environment:

```yaml
environments:
  development:
    log_level: "DEBUG"
    backup_enabled: false
    monitoring_enabled: false
    
  staging:
    log_level: "INFO"
    backup_enabled: true
    monitoring_enabled: true
    
  production:
    log_level: "WARNING"
    backup_enabled: true
    monitoring_enabled: true
    security:
      read_only_root: true
      no_new_privileges: true
```

## 🚀 Deployment Workflows

### Development Deployment

```bash
# Local development
make docker-run

# With hot reload
make docker-run
# Edit code, containers auto-restart
```

### Staging Deployment

```bash
# Deploy to staging
make deploy-staging

# Check status
make status

# View logs
make logs
```

### Production Deployment

```bash
# Automated production deployment
make deploy-auto

# Manual production deployment
make prod-deploy

# Monitor deployment
make health-monitor
```

## 📊 Health Monitoring

### Continuous Monitoring

The health monitor runs continuously and:

1. **Checks Health Endpoints** - Every 60 seconds
2. **Monitors System Resources** - CPU, memory, disk usage
3. **Takes Recovery Actions** - Restart containers on failures
4. **Sends Alerts** - Discord, email, or syslog notifications

### Health Check Endpoints

- **`/health`** - Basic health status
- **`/metrics`** - Prometheus metrics
- **`/status`** - Detailed bot status

### Recovery Actions

1. **Container Restart** - Automatic restart on failures
2. **Backup Creation** - Data backup before actions
3. **Alert Notifications** - Immediate notification of issues
4. **Log Analysis** - Error log review and reporting

## 🔒 Security Features

### Security Scanning

```bash
# Run Bandit security scan
make ci-security

# Check dependencies
safety check

# Run all security checks
make ci-security
```

### Production Security

- **Read-only root filesystem** (except data directory)
- **No new privileges** policy
- **Resource limits** and monitoring
- **Secure logging** configuration

## 📈 Monitoring & Alerting

### Prometheus Integration

```yaml
# Prometheus configuration
scrape_configs:
  - job_name: 'discord-bot'
    static_configs:
      - targets: ['discord-bot:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

### Grafana Dashboards

- **Bot Health** - Overall status and metrics
- **Performance** - Response times and throughput
- **Resources** - CPU, memory, and disk usage
- **Alerts** - Historical alert data

### Alert Channels

1. **Discord Webhook** - Real-time notifications
2. **Email Alerts** - Admin notifications
3. **System Logs** - Fallback logging
4. **Custom Integrations** - Extensible alert system

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
jobs:
  test:           # Run test suite
  security:       # Security scanning
  build:          # Docker image build
  deploy-staging: # Staging deployment
  deploy-production: # Production deployment
  monitoring:     # Setup monitoring
```

### Automated Testing

- **Unit Tests** - Core module testing
- **Integration Tests** - End-to-end validation
- **Security Tests** - Vulnerability scanning
- **Performance Tests** - Load and stress testing

### Deployment Gates

1. **Test Passing** - All tests must pass
2. **Security Clear** - No security vulnerabilities
3. **Code Quality** - Linting and formatting checks
4. **Health Checks** - Post-deployment validation

## 🛠️ Troubleshooting

### Common Issues

#### Health Check Failures

```bash
# Check container status
make status

# View container logs
make logs

# Run manual health check
make health-check

# Restart containers
make docker-stop
make docker-run
```

#### Deployment Failures

```bash
# Check prerequisites
docker --version
docker-compose --version

# Verify configuration
cat .env

# Clean and redeploy
make docker-clean
make deploy
```

#### Monitoring Issues

```bash
# Check Prometheus
curl http://localhost:9090/-/healthy

# Check Grafana
curl http://localhost:3000/api/health

# View monitoring logs
docker-compose logs prometheus grafana
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
make deploy -v

# Check detailed status
docker-compose ps -a
```

## 📚 Advanced Usage

### Custom Deployment Scripts

```bash
# Create custom deployment
./scripts/deploy.sh custom-env

# Custom health monitoring
./scripts/health-monitor.sh -e http://localhost:9000 -i 30

# Custom alerts
./scripts/send-alert.sh -w "webhook_url" "Custom message"
```

### Environment-Specific Configurations

```bash
# Override configuration
export DEPLOYMENT_ENV=production
export BACKUP_ENABLED=true
export MONITORING_ENABLED=true

# Run deployment
make deploy-auto
```

### Backup and Recovery

```bash
# Create backup
make backup

# Restore from backup
make restore BACKUP_FILE=backup-20241201-143022.tar.gz

# List available backups
ls -la backups/
```

## 🔮 Future Enhancements

### Planned Features

- **Kubernetes Deployment** - K8s manifests and operators
- **Multi-Region Deployment** - Geographic distribution
- **Advanced Rollback** - Automated rollback strategies
- **Performance Optimization** - Auto-scaling and load balancing
- **Security Hardening** - Additional security measures

### Contributing

To contribute to the deployment automation:

1. **Fork the repository**
2. **Create a feature branch**
3. **Implement your changes**
4. **Add tests and documentation**
5. **Submit a pull request**

## 📞 Support

### Getting Help

- **Documentation** - Check this guide and README.md
- **Issues** - Report bugs on GitHub
- **Discussions** - Ask questions in GitHub Discussions
- **Logs** - Check application and deployment logs

### Emergency Procedures

1. **Immediate Rollback**
   ```bash
   make docker-stop
   make restore BACKUP_FILE=latest_backup.tar.gz
   make docker-run
   ```

2. **Health Emergency**
   ```bash
   make health-monitor
   # Monitor and take action as needed
   ```

3. **Contact Support**
   - Check logs in `/data/bot.log`
   - Review health monitor logs
   - Contact system administrator

---

**Note**: This deployment automation system is designed for production use and includes comprehensive monitoring, alerting, and recovery mechanisms. Always test deployments in staging environments before production deployment.
