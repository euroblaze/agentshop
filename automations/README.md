# AgentShop Automations

This directory contains automation scripts and tools for the AgentShop platform, including web crawling, data processing, scheduling, and notifications.

## Directory Structure

```
automations/
├── webcrawlers/           # Web crawling and data scraping
│   ├── scoup_client.py    # Integration with Scoup microservice
│   └── scrapers/          # Custom scraping utilities
├── schedulers/            # Task scheduling and automation
│   ├── automation_scheduler.py  # Main scheduler
│   └── scheduler_config.json   # Task configurations
├── data_processors/       # Data processing and analysis
│   ├── llm_data_processor.py   # LLM-powered data analysis
│   └── processors/        # Custom data processors
├── notifications/         # Notification and alerting systems
│   ├── email_notifier.py  # Email notifications
│   ├── slack_notifier.py  # Slack integration
│   └── webhook_notifier.py # Webhook notifications
└── logs/                  # Automation logs
```

## Features

### Web Crawling
- **Scoup Integration**: Connect to the Scoup microservice for advanced web scraping
- **Preset Configurations**: Ready-to-use configs for e-commerce, blogs, social media
- **Batch Processing**: Scrape multiple URLs with controlled concurrency
- **Data Storage**: Automatic saving to data lake with organized structure

### Scheduling
- **Cron-like Scheduling**: Support for daily, weekly, hourly, and custom schedules
- **Task Management**: Add, remove, update, and monitor scheduled tasks
- **Error Handling**: Comprehensive error tracking and retry mechanisms
- **Status Monitoring**: Real-time task status and execution history

### 🧠 Data Processing
- **LLM Analysis**: Use AI to analyze scraped content and generate insights
- **Content Analysis**: Extract topics, themes, and key information
- **Sentiment Analysis**: Analyze sentiment of text content
- **Summarization**: Generate concise summaries of large content
- **Keyword Extraction**: Identify important keywords and phrases

###  Notifications
- **Multi-channel**: Email, Slack, webhooks, and custom integrations
- **Event-driven**: Trigger notifications based on automation events
- **Templates**: Customizable notification templates
- **Rate Limiting**: Prevent notification spam

## Quick Start

### 1. Setup Scoup Microservice

First, set up the Scoup microservice for web crawling:

```bash
# Clone and setup Scoup
git clone https://github.com/euroblaze/scoup.git
cd scoup
npm install
npm start
```

### 2. Configure Environment

```bash
# Add to your .env file
SCOUP_BASE_URL=http://localhost:3001
SCOUP_API_KEY=your_api_key_here
NOTIFICATION_EMAIL_SMTP_HOST=smtp-relay.brevo.com
NOTIFICATION_EMAIL_USER=your-brevo-login@example.com
NOTIFICATION_EMAIL_PASS=your-brevo-smtp-key
```

### 3. Start the Automation Scheduler

```bash
cd automations/schedulers
python automation_scheduler.py
```

## Usage Examples

### Web Crawling with Scoup

```python
from automations.webcrawlers.scoup_client import ScoupClient, ScrapeRequest

async def crawl_competitor():
    config = ScoupConfig(base_url="http://localhost:3001")
    
    async with ScoupClient(config) as client:
        request = ScrapeRequest(
            url="https://competitor.com/products",
            javascript=True,
            custom_selectors={
                'price': '.price',
                'title': '.product-title',
                'description': '.description'
            }
        )
        
        result = await client.scrape_url(request)
        print(f"Scraped: {result.title}")
```

### Scheduling Automation Tasks

```python
from automations.schedulers.automation_scheduler import AutomationScheduler

scheduler = AutomationScheduler()

# Add daily competitor analysis
scheduler.add_task(
    task_id="daily_competitor_check",
    name="Daily Competitor Analysis",
    task_type="webcrawl",
    schedule_expression="daily",
    config={
        "target_url": "https://competitor.com",
        "job_type": "competitor_analysis"
    }
)

scheduler.start()
```

### LLM Data Processing

```python
from automations.data_processors.llm_data_processor import LLMDataProcessor

processor = LLMDataProcessor()

# Analyze scraped content
result = await processor.process_batch(
    input_path="datalake/scraped_data",
    output_path="datalake/processed_data",
    processing_type="content_analysis",
    config={
        'llm_provider': 'openai',
        'max_files': 50
    }
)

print(f"Processed {result.processed_items} items")
print(f"Summary: {result.summary}")
```

## Automation Types

### 1. Web Crawling Jobs

**Competitor Analysis**
- Monitor competitor pricing and features
- Track new product launches
- Analyze marketing strategies
- Capture website changes

**Market Research**
- Scrape industry news and reports
- Monitor trend discussions
- Collect customer feedback
- Track regulatory changes

**Content Aggregation**
- Collect blog posts and articles
- Monitor social media mentions
- Aggregate user-generated content
- Track brand sentiment

### 2. Data Processing Tasks

**Content Analysis**
- Extract key topics and themes
- Identify business opportunities
- Assess content quality
- Generate actionable insights

**Sentiment Analysis**
- Analyze customer feedback sentiment
- Monitor brand perception
- Track sentiment trends
- Identify issues early

**Summarization**
- Create executive summaries
- Generate content briefs
- Produce research digests
- Build knowledge bases

### 3. Scheduled Operations

**Daily Tasks**
- Competitor price monitoring
- News and updates collection
- Data quality checks
- Performance analysis

**Weekly Tasks**
- Comprehensive market analysis
- Trend reporting
- Data archival
- System maintenance

**Monthly Tasks**
- Strategic analysis reports
- Performance benchmarking
- Cost optimization review
- Capacity planning

## Configuration

### Scheduler Configuration

```json
{
  "tasks": [
    {
      "id": "competitor_analysis_daily",
      "name": "Daily Competitor Analysis",
      "task_type": "webcrawl",
      "schedule_expression": "daily",
      "config": {
        "target_url": "https://competitor.com",
        "job_type": "competitor_analysis",
        "scrape_config": {
          "extract_pricing": true,
          "extract_features": true,
          "screenshot": true
        }
      },
      "is_active": true
    }
  ]
}
```

### Scoup Configuration

```python
config = ScoupConfig(
    base_url="http://localhost:3001",
    api_key="your_api_key",
    timeout=30,
    max_retries=3,
    rate_limit=10
)
```

## Monitoring and Logging

### Task Status Monitoring

```python
scheduler = AutomationScheduler()
status = scheduler.get_task_status()

for task in status:
    print(f"Task: {task['name']}")
    print(f"Status: {'Active' if task['is_active'] else 'Inactive'}")
    print(f"Runs: {task['run_count']}, Errors: {task['error_count']}")
```

### Log Files

- `automations/logs/scheduler.log` - Scheduler operations
- `automations/logs/webcrawler.log` - Web crawling activities
- `automations/logs/processor.log` - Data processing logs
- `automations/logs/notifications.log` - Notification events

### Health Checks

```python
# Check Scoup service health
async with ScoupClient() as client:
    healthy = await client.health_check()
    print(f"Scoup service: {'[HEALTHY]' if healthy else '[DOWN]'}")

# Check LLM processor health
processor = LLMDataProcessor()
# Health check would verify LLM provider connectivity
```

## Error Handling

### Retry Mechanisms
- Automatic retries for failed web requests
- Exponential backoff for rate limiting
- Circuit breaker pattern for service failures

### Error Notifications
- Immediate alerts for critical failures
- Daily summaries of automation issues
- Escalation procedures for persistent problems

### Data Recovery
- Automatic backup of processed data
- Recovery procedures for partial failures
- Data validation and quality checks

## Security Considerations

### API Key Management
- Secure storage of third-party API keys
- Key rotation procedures
- Access logging and monitoring

### Data Privacy
- Anonymization of personal data
- Compliance with data protection regulations
- Secure data transmission and storage

### Access Control
- Role-based access to automation tools
- Audit trails for automation activities
- Secure configuration management

## Performance Optimization

### Efficient Processing
- Parallel processing for batch operations
- Memory management for large datasets
- Caching for frequently accessed data

### Resource Management
- CPU and memory monitoring
- Automatic scaling based on workload
- Cost optimization for cloud resources

### Rate Limiting
- Respectful crawling of external sites
- API rate limit compliance
- Load balancing across providers

## Integration Points

### With AgentShop Core
- Database integration for storing results
- LLM service integration for analysis
- User authentication and authorization

### With External Services
- Scoup microservice for web crawling
- LLM providers for content analysis
- Notification services for alerts

### With Data Lake
- Structured data storage
- Metadata management
- Data lineage tracking

## Best Practices

### Crawling Ethics
- Respect robots.txt files
- Implement reasonable delays
- Avoid overloading target servers
- Monitor for IP blocking

### Data Quality
- Validate scraped data
- Implement data cleansing
- Track data source reliability
- Maintain data freshness

### Operational Excellence
- Regular monitoring and alerting
- Proactive error handling
- Performance optimization
- Documentation and knowledge sharing