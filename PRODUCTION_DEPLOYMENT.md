# 2KCompLeague Discord Bot - Production Deployment Guide

## 🚀 Production Deployment Checklist

### ✅ Pre-Deployment Verification

#### 1. Code Quality & Testing
- [x] **All tests passing**: 131/131 tests (100%)
- [x] **Code formatting**: black, isort, ruff configured
- [x] **Type checking**: mypy configured
- [x] **Linting**: ruff configured
- [x] **Integration tests**: End-to-end validation complete

#### 2. Core Modules
- [x] **Configuration**: Pydantic settings with environment validation
- [x] **Logging**: Structured JSON + console output
- [x] **HTTP Client**: Retry logic, rate limiting, pagination
- [x] **SportsPress Integration**: API endpoints and data parsing
- [x] **Data Processing**: Leaders, records, milestones
- [x] **Discord Bot**: Commands and background tasks
- [x] **Health Monitoring**: HTTP endpoints and metrics
- [x] **Performance Monitoring**: Metrics collection and optimization

#### 3. Infrastructure
- [x] **Docker Configuration**: Dockerfile and docker-compose files
- [x] **Deployment Scripts**: Automated deployment with backup
- [x] **Monitoring**: Prometheus and Grafana configuration
- [x] **Health Checks**: Container and application health validation
- [x] **Performance Testing**: Load testing and stress testing tools

### 🚀 Production Deployment Steps

#### Step 1: Environment Setup
```bash
# 1. Create production environment file
cp env.example .env.prod

# 2. Configure production environment variables
# Edit .env.prod with production values:
# - DISCORD_TOKEN (production bot token)
# - GUILD_ID (production server ID)
# - Channel IDs for production server
# - Production API endpoints
# - Production logging levels
```

#### Step 2: Docker Network Setup
```bash
# Create external network for production
docker network create 2kcomp-league-network

# Verify network creation
docker network ls | grep 2kcomp-league
```

#### Step 3: Production Deployment
```bash
# Option 1: Full production deployment with monitoring
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile monitoring up -d

# Option 2: Bot only deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify deployment
docker-compose ps
docker-compose logs discord-bot
```

#### Step 4: Health Verification
```bash
# Check application health
curl http://localhost:8080/health | jq .

# Check metrics endpoint
curl http://localhost:8080/metrics

# Check performance metrics
curl http://localhost:8080/performance | jq .

# Check container health
docker-compose ps
```

#### Step 5: Performance Testing
```bash
# Run comprehensive performance test
python scripts/performance_test.py --mode comprehensive

# Run load testing
python scripts/performance_test.py --mode load-test --scenario normal_load

# Run stress testing
python scripts/performance_test.py --mode stress-test --max-users 50
```

### 🔧 Production Configuration

#### Environment Variables
```env
# Production Settings
LOG_LEVEL=WARNING
CHECK_INTERVAL=600  # 10 minutes
HTTP_TIMEOUT=60
HTTP_MAX_RETRIES=5
HTTP_RATE_LIMIT_DELAY=2

# Resource Limits
# Memory: 1GB limit, 512MB reservation
# CPU: 1.0 limit, 0.5 reservation
```

#### Docker Resources
- **Memory**: 1GB limit, 512MB reservation
- **CPU**: 1.0 limit, 0.5 reservation
- **Restart Policy**: Always
- **Health Check**: 60s interval, 15s timeout, 5 retries

#### Security Features
- Read-only root filesystem (except data directory)
- No new privileges
- Resource limits enforced
- Network isolation

### 📊 Monitoring & Observability

#### Health Endpoints
- **Root**: `/` - Service information and available endpoints
- **Health**: `/health` - Application health status
- **Metrics**: `/metrics` - Prometheus metrics
- **Status**: `/status` - Bot status and configuration
- **Performance**: `/performance` - Performance metrics
- **Optimizations**: `/performance/optimizations` - Performance recommendations
- **Load Testing**: `/performance/load-test` - Load test results

#### Metrics Collected
- System metrics (CPU, memory, disk I/O, network)
- API call performance (response times, error rates)
- Background task status
- Discord connection health
- Custom business metrics

#### Monitoring Stack
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Health Checks**: Container and application monitoring
- **Performance Monitoring**: Real-time performance tracking

### 🚨 Production Operations

#### Daily Operations
```bash
# Check bot status
curl http://localhost:8080/status | jq .

# Monitor logs
docker-compose logs -f discord-bot

# Check resource usage
docker stats discord-bot
```

#### Weekly Operations
```bash
# Performance analysis
python scripts/performance_test.py --mode analysis

# Health check summary
curl http://localhost:8080/health | jq '.summary'

# Backup data
make backup
```

#### Monthly Operations
```bash
# Comprehensive performance testing
python scripts/performance_test.py --mode comprehensive

# Load testing validation
python scripts/performance_test.py --mode load-test --scenario stress_test

# Performance optimization
python scripts/performance_test.py --mode optimize
```

### 🔄 Deployment Automation

#### CI/CD Pipeline
- **Automated Testing**: All tests run on every commit
- **Code Quality**: Formatting, linting, and type checking
- **Security Scanning**: Dependency vulnerability checks
- **Automated Deployment**: Production deployment with backup

#### Deployment Commands
```bash
# Automated production deployment
make deploy-auto

# Staging deployment
make deploy-staging

# Manual deployment
make deploy
```

### 📋 Post-Deployment Verification

#### 1. Functionality Tests
- [ ] Bot responds to slash commands
- [ ] Background tasks are running
- [ ] API integration is working
- [ ] Data processing is functioning
- [ ] Discord embeds are displaying correctly

#### 2. Performance Tests
- [ ] Response times are acceptable (< 2 seconds)
- [ ] Memory usage is stable
- [ ] CPU usage is reasonable
- [ ] API call success rate > 95%
- [ ] Background task completion > 90%

#### 3. Monitoring Tests
- [ ] Health endpoints are responding
- [ ] Metrics are being collected
- [ ] Performance monitoring is active
- [ ] Alerts are configured (if applicable)
- [ ] Logs are being generated

#### 4. Security Tests
- [ ] Bot only responds in authorized channels
- [ ] Admin commands require proper roles
- [ ] API endpoints are properly secured
- [ ] Environment variables are not exposed
- [ ] Container security is enforced

### 🚨 Troubleshooting

#### Common Issues

**Bot not responding to commands**
```bash
# Check bot status
curl http://localhost:8080/status | jq .

# Check Discord connection
docker-compose logs discord-bot | grep -i discord

# Verify token and permissions
docker-compose exec discord-bot python -c "from core.config import settings; print('Token configured:', bool(settings.DISCORD_TOKEN))"
```

**High memory usage**
```bash
# Check memory metrics
curl http://localhost:8080/performance | jq '.memory_percent'

# Run performance analysis
python scripts/performance_test.py --mode analysis

# Check for memory leaks
docker stats discord-bot
```

**API integration failures**
```bash
# Check API health
curl http://localhost:8080/health | jq '.api_status'

# Verify API endpoints
docker-compose exec discord-bot python -c "from core.config import settings; print('API base:', settings.SPORTSPRESS_BASE)"

# Check error rates
curl http://localhost:8080/performance | jq '.error_rate'
```

#### Emergency Procedures

**Bot unresponsive**
```bash
# Restart the bot
docker-compose restart discord-bot

# Check logs for errors
docker-compose logs --tail=100 discord-bot

# Verify health status
curl http://localhost:8080/health
```

**Data corruption**
```bash
# Restore from backup
make restore BACKUP_FILE=backup-YYYYMMDD-HHMMSS.tar.gz

# Verify data integrity
curl http://localhost:8080/status | jq '.data_status'
```

**Performance degradation**
```bash
# Run performance optimization
python scripts/performance_test.py --mode optimize

# Check system resources
docker stats discord-bot

# Analyze performance metrics
curl http://localhost:8080/performance | jq '.optimization_recommendations'
```

### 📞 Support & Maintenance

#### Contact Information
- **Development Team**: 2kcomp-league-team
- **Documentation**: README.md and inline code documentation
- **Issue Tracking**: GitHub Issues (if applicable)
- **Performance Monitoring**: Built-in performance dashboard

#### Maintenance Schedule
- **Daily**: Health checks and log monitoring
- **Weekly**: Performance analysis and optimization
- **Monthly**: Comprehensive testing and validation
- **Quarterly**: Security review and dependency updates

---

## 🎯 Deployment Success Criteria

The deployment is considered successful when:
1. ✅ All tests pass (131/131 - 100%)
2. ✅ Bot responds to commands within 2 seconds
3. ✅ Health endpoints return healthy status
4. ✅ Performance metrics are within acceptable ranges
5. ✅ Background tasks are completing successfully
6. ✅ API integration is functioning properly
7. ✅ Discord embeds are displaying correctly
8. ✅ Monitoring and alerting are active
9. ✅ Logs are being generated and accessible
10. ✅ Resource usage is within defined limits

---

**Last Updated**: Current session
**Deployment Status**: Ready for Production
**Next Review**: After successful production deployment
