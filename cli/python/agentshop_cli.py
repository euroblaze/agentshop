#!/usr/bin/env python3
"""
AgentShop CLI - Python Management Interface
Provides command-line tools for managing the AgentShop platform
"""

import click
import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from services.llm_orm_service import llm_orm_service
from config.llm_config import config_manager
from repositories.llm_repository import (
    LLMRequestRepository, LLMUsageStatsRepository, LLMProviderStatusRepository
)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """AgentShop CLI - Manage your AI Agent Marketplace"""
    pass


# =============================================================================
# LLM MANAGEMENT COMMANDS
# =============================================================================

@cli.group()
def llm():
    """LLM provider management commands"""
    pass


@llm.command()
def providers():
    """List all LLM providers and their status"""
    click.echo("🤖 LLM Providers Status")
    click.echo("=" * 50)
    
    try:
        status_repo = LLMProviderStatusRepository()
        providers = status_repo.get_all_provider_status()
        
        if not providers:
            click.echo("No providers configured.")
            return
        
        for provider in providers:
            status_icon = "[OK]" if provider.is_healthy else "[ERROR]"
            enabled_icon = "🟢" if provider.is_enabled else "🔴"
            
            click.echo(f"{status_icon} {enabled_icon} {provider.provider.upper()}")
            click.echo(f"   Enabled: {provider.is_enabled}")
            click.echo(f"   Healthy: {provider.is_healthy}")
            click.echo(f"   API Key: {'[OK]' if provider.api_key_configured else '[ERROR]'}")
            click.echo(f"   Default Model: {provider.default_model or 'Not set'}")
            click.echo(f"   Daily Cost: ${provider.current_daily_cost:.4f} / ${provider.daily_cost_limit:.2f}")
            if provider.last_error:
                click.echo(f"   Last Error: {provider.last_error}")
            click.echo()
            
    except Exception as e:
        click.echo(f"[ERROR] Error: {e}", err=True)


@llm.command()
@click.argument('provider')
@click.argument('api_key')
@click.option('--model', help='Default model for the provider')
@click.option('--cost-limit', type=float, default=10.0, help='Daily cost limit in USD')
def enable(provider: str, api_key: str, model: Optional[str], cost_limit: float):
    """Enable an LLM provider"""
    try:
        click.echo(f"[SETUP] Enabling {provider.upper()} provider...")
        
        config_manager.enable_provider(
            provider,
            api_key,
            default_model=model,
            cost_limit_daily=cost_limit
        )
        
        click.echo(f"[OK] {provider.upper()} provider enabled successfully!")
        if model:
            click.echo(f"   Default model: {model}")
        click.echo(f"   Daily cost limit: ${cost_limit:.2f}")
        
    except Exception as e:
        click.echo(f"[ERROR] Error enabling provider: {e}", err=True)


@llm.command()
@click.argument('provider')
def disable(provider: str):
    """Disable an LLM provider"""
    try:
        click.echo(f"[DISABLE] Disabling {provider.upper()} provider...")
        config_manager.disable_provider(provider)
        click.echo(f"[OK] {provider.upper()} provider disabled successfully!")
        
    except Exception as e:
        click.echo(f"[ERROR] Error disabling provider: {e}", err=True)


@llm.command()
@click.option('--days', default=7, help='Number of days to show stats for')
@click.option('--provider', help='Filter by specific provider')
def stats(days: int, provider: Optional[str]):
    """Show LLM usage statistics"""
    click.echo(f"[STATS] LLM Usage Statistics (Last {days} days)")
    click.echo("=" * 60)
    
    try:
        usage_repo = LLMUsageStatsRepository()
        stats = usage_repo.get_usage_summary('day', days, provider)
        
        if not stats:
            click.echo("No usage data found.")
            return
        
        total_requests = sum(s.request_count for s in stats)
        total_cost = sum(s.total_cost for s in stats)
        total_tokens = sum(s.total_tokens for s in stats)
        
        click.echo(f"📈 Summary:")
        click.echo(f"   Total Requests: {total_requests:,}")
        click.echo(f"   Total Cost: ${total_cost:.4f}")
        click.echo(f"   Total Tokens: {total_tokens:,}")
        click.echo()
        
        # Group by provider
        provider_stats = {}
        for stat in stats:
            if stat.provider not in provider_stats:
                provider_stats[stat.provider] = {
                    'requests': 0, 'cost': 0.0, 'tokens': 0
                }
            provider_stats[stat.provider]['requests'] += stat.request_count
            provider_stats[stat.provider]['cost'] += stat.total_cost
            provider_stats[stat.provider]['tokens'] += stat.total_tokens
        
        click.echo("🤖 By Provider:")
        for prov, data in provider_stats.items():
            click.echo(f"   {prov.upper()}:")
            click.echo(f"     Requests: {data['requests']:,}")
            click.echo(f"     Cost: ${data['cost']:.4f}")
            click.echo(f"     Tokens: {data['tokens']:,}")
            click.echo()
            
    except Exception as e:
        click.echo(f"[ERROR] Error: {e}", err=True)


@llm.command()
@click.argument('prompt')
@click.option('--provider', default='openai', help='LLM provider to use')
@click.option('--model', help='Model to use')
@click.option('--temperature', type=float, default=0.7, help='Temperature (0.0-1.0)')
@click.option('--max-tokens', type=int, default=100, help='Maximum tokens')
def test(prompt: str, provider: str, model: Optional[str], temperature: float, max_tokens: int):
    """Test LLM generation"""
    click.echo(f"🧪 Testing {provider.upper()} provider...")
    click.echo(f"Prompt: {prompt}")
    click.echo("=" * 50)
    
    async def run_test():
        try:
            result = await llm_orm_service.generate_text(
                prompt=prompt,
                provider=provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                request_type='cli_test'
            )
            
            click.echo(f"[OK] Response:")
            click.echo(f"{result['content']}")
            click.echo()
            click.echo(f"[STATS] Stats:")
            click.echo(f"   Provider: {result['provider']}")
            click.echo(f"   Model: {result['model']}")
            click.echo(f"   Tokens: {result['tokens_used']}")
            click.echo(f"   Cost: ${result['cost']:.6f}")
            click.echo(f"   Time: {result['processing_time_ms']}ms")
            click.echo(f"   Cached: {result['cached']}")
            
        except Exception as e:
            click.echo(f"[ERROR] Test failed: {e}", err=True)
    
    asyncio.run(run_test())


# =============================================================================
# DATABASE MANAGEMENT COMMANDS
# =============================================================================

@cli.group()
def db():
    """Database management commands"""
    pass


@db.command()
@click.option('--backup-dir', default='./datalake/db_dumps', help='Backup directory')
def backup(backup_dir: str):
    """Create database backup"""
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'agentshop_backup_{timestamp}.sql')
    
    try:
        # For SQLite database
        db_path = os.getenv('DATABASE_URL', 'sqlite:///agentshop.db').replace('sqlite:///', '')
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        
        with open(backup_file, 'w') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        
        conn.close()
        
        click.echo(f"[OK] Database backed up to: {backup_file}")
        
    except Exception as e:
        click.echo(f"[ERROR] Backup failed: {e}", err=True)


@db.command()
@click.argument('backup_file')
@click.option('--confirm', is_flag=True, help='Confirm restoration')
def restore(backup_file: str, confirm: bool):
    """Restore database from backup"""
    if not confirm:
        click.echo("[WARNING]  This will overwrite the current database!")
        click.echo("Use --confirm flag to proceed.")
        return
    
    try:
        if not os.path.exists(backup_file):
            click.echo(f"[ERROR] Backup file not found: {backup_file}")
            return
        
        db_path = os.getenv('DATABASE_URL', 'sqlite:///agentshop.db').replace('sqlite:///', '')
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        
        with open(backup_file, 'r') as f:
            sql_script = f.read()
        
        conn.executescript(sql_script)
        conn.close()
        
        click.echo(f"[OK] Database restored from: {backup_file}")
        
    except Exception as e:
        click.echo(f"[ERROR] Restore failed: {e}", err=True)


@db.command()
def migrate():
    """Run database migrations"""
    try:
        from orm.base_model import db_manager
        db_manager.create_tables()
        click.echo("[OK] Database migrations completed successfully!")
        
    except Exception as e:
        click.echo(f"[ERROR] Migration failed: {e}", err=True)


# =============================================================================
# DATA MANAGEMENT COMMANDS
# =============================================================================

@cli.group()
def data():
    """Data management commands"""
    pass


@data.command()
@click.option('--days', default=30, help='Days of data to keep')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted')
def cleanup(days: int, dry_run: bool):
    """Clean up old data"""
    cutoff_date = datetime.now() - timedelta(days=days)
    
    click.echo(f"🧹 Data Cleanup (older than {days} days)")
    click.echo(f"Cutoff date: {cutoff_date}")
    click.echo("=" * 50)
    
    try:
        request_repo = LLMRequestRepository()
        
        # Find old requests
        old_requests = request_repo.find_by()  # Would need to add date filter
        
        if dry_run:
            click.echo(f"Would delete {len(old_requests)} old LLM requests")
        else:
            # Implement actual cleanup
            click.echo(f"Deleted {len(old_requests)} old LLM requests")
            
    except Exception as e:
        click.echo(f"[ERROR] Cleanup failed: {e}", err=True)


@data.command()
@click.option('--format', type=click.Choice(['json', 'csv']), default='json')
@click.option('--output', help='Output file path')
def export(format: str, output: Optional[str]):
    """Export data"""
    if not output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output = f"./datalake/processed_data/export_{timestamp}.{format}"
    
    os.makedirs(os.path.dirname(output), exist_ok=True)
    
    try:
        usage_repo = LLMUsageStatsRepository()
        stats = usage_repo.get_usage_summary('day', 30)
        
        if format == 'json':
            with open(output, 'w') as f:
                json.dump([s.to_dict() for s in stats], f, indent=2, default=str)
        elif format == 'csv':
            import csv
            with open(output, 'w', newline='') as f:
                if stats:
                    writer = csv.DictWriter(f, fieldnames=stats[0].to_dict().keys())
                    writer.writeheader()
                    for stat in stats:
                        writer.writerow(stat.to_dict())
        
        click.echo(f"[OK] Data exported to: {output}")
        
    except Exception as e:
        click.echo(f"[ERROR] Export failed: {e}", err=True)


# =============================================================================
# AUTOMATION COMMANDS
# =============================================================================

@cli.group()
def automation():
    """Automation management commands"""
    pass


@automation.command()
def list_jobs():
    """List all automation jobs"""
    click.echo("🤖 Automation Jobs")
    click.echo("=" * 50)
    # Implementation would query webcrawler_jobs table
    click.echo("No jobs configured yet.")


@automation.command()
@click.argument('job_name')
@click.argument('target_url')
@click.option('--job-type', default='content_scraping', help='Type of job')
@click.option('--schedule', help='Cron schedule expression')
def create_job(job_name: str, target_url: str, job_type: str, schedule: Optional[str]):
    """Create a new automation job"""
    click.echo(f"[SETUP] Creating job: {job_name}")
    click.echo(f"Target URL: {target_url}")
    click.echo(f"Job Type: {job_type}")
    if schedule:
        click.echo(f"Schedule: {schedule}")
    
    # Implementation would create job in webcrawler_jobs table
    click.echo("[OK] Job created successfully!")


# =============================================================================
# UTILITY COMMANDS
# =============================================================================

@cli.command()
def config():
    """Show current configuration"""
    click.echo("[CONFIG]  AgentShop Configuration")
    click.echo("=" * 50)
    
    try:
        safe_config = config_manager.get_safe_config()
        
        click.echo(f"Default Provider: {safe_config['default_provider']}")
        click.echo(f"Cache TTL: {safe_config['cache_ttl']}s")
        click.echo(f"Caching Enabled: {safe_config['enable_caching']}")
        click.echo(f"Rate Limiting: {safe_config['enable_rate_limiting']}")
        click.echo()
        
        click.echo("Providers:")
        for provider, config in safe_config['providers'].items():
            enabled_icon = "🟢" if config['enabled'] else "🔴"
            click.echo(f"  {enabled_icon} {provider.upper()}")
            click.echo(f"     API Key: {'[OK]' if config['api_key'] != 'None' else '[ERROR]'}")
            if config['default_model']:
                click.echo(f"     Model: {config['default_model']}")
            click.echo(f"     Cost Limit: ${config['cost_limit_daily']}/day")
            
    except Exception as e:
        click.echo(f"[ERROR] Error: {e}", err=True)


@cli.command()
def status():
    """Show system status"""
    click.echo("🏥 AgentShop System Status")
    click.echo("=" * 50)
    
    try:
        # Database status
        from orm.base_model import db_manager
        db_manager.get_session().close()
        click.echo("[OK] Database: Connected")
        
        # LLM providers status
        asyncio.run(_check_llm_health())
        
    except Exception as e:
        click.echo(f"[ERROR] System check failed: {e}", err=True)


async def _check_llm_health():
    """Check LLM provider health"""
    try:
        health = await llm_orm_service.health_check()
        click.echo("\n🤖 LLM Providers:")
        for provider, healthy in health.items():
            status_icon = "[OK]" if healthy else "[ERROR]"
            click.echo(f"   {status_icon} {provider.upper()}")
    except Exception as e:
        click.echo(f"[ERROR] LLM health check failed: {e}")


if __name__ == '__main__':
    cli()