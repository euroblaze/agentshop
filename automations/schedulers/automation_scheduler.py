#!/usr/bin/env python3
"""
Automation Scheduler - Manages scheduled tasks and automations
Handles cron-like scheduling for various automation tasks
"""

import asyncio
import schedule
import time
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import logging

# Add backend to path for database integration
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from automations.webcrawlers.scoup_client import ScoupJobManager
from automations.data_processors.llm_data_processor import LLMDataProcessor


@dataclass
class ScheduledTask:
    """Represents a scheduled automation task"""
    id: str
    name: str
    task_type: str  # 'webcrawl', 'data_process', 'llm_analysis', 'report_gen'
    schedule_expression: str  # e.g., "daily", "weekly", "0 */6 * * *"
    config: Dict[str, Any]
    is_active: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None


class AutomationScheduler:
    """Manages and executes scheduled automation tasks"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), 'scheduler_config.json'
        )
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize processors
        self.scoup_manager = ScoupJobManager()
        self.llm_processor = LLMDataProcessor()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('automations/logs/scheduler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Load existing tasks
        self.load_tasks()
    
    def load_tasks(self):
        """Load tasks from configuration file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                for task_data in data.get('tasks', []):
                    task = ScheduledTask(**task_data)
                    self.tasks[task.id] = task
                    
                self.logger.info(f"Loaded {len(self.tasks)} tasks from configuration")
            except Exception as e:
                self.logger.error(f"Failed to load tasks: {e}")
    
    def save_tasks(self):
        """Save tasks to configuration file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            data = {
                'tasks': [asdict(task) for task in self.tasks.values()],
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
            self.logger.info(f"Saved {len(self.tasks)} tasks to configuration")
        except Exception as e:
            self.logger.error(f"Failed to save tasks: {e}")
    
    def add_task(
        self,
        task_id: str,
        name: str,
        task_type: str,
        schedule_expression: str,
        config: Dict[str, Any]
    ) -> ScheduledTask:
        """Add a new scheduled task"""
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            task_type=task_type,
            schedule_expression=schedule_expression,
            config=config
        )
        
        self.tasks[task_id] = task
        self._schedule_task(task)
        self.save_tasks()
        
        self.logger.info(f"Added task: {name} ({task_type})")
        return task
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            schedule.clear(task_id)
            del self.tasks[task_id]
            self.save_tasks()
            
            self.logger.info(f"Removed task: {task.name}")
            return True
        
        return False
    
    def update_task(self, task_id: str, **kwargs) -> bool:
        """Update a scheduled task"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            # Re-schedule if schedule expression changed
            if 'schedule_expression' in kwargs:
                schedule.clear(task_id)
                self._schedule_task(task)
            
            self.save_tasks()
            self.logger.info(f"Updated task: {task.name}")
            return True
        
        return False
    
    def _schedule_task(self, task: ScheduledTask):
        """Schedule a task using the schedule library"""
        if not task.is_active:
            return
        
        schedule_expr = task.schedule_expression.lower()
        
        try:
            if schedule_expr == "daily":
                schedule.every().day.at("02:00").do(
                    self._run_task_wrapper, task.id
                ).tag(task.id)
            elif schedule_expr == "weekly":
                schedule.every().sunday.at("01:00").do(
                    self._run_task_wrapper, task.id
                ).tag(task.id)
            elif schedule_expr == "hourly":
                schedule.every().hour.do(
                    self._run_task_wrapper, task.id
                ).tag(task.id)
            elif schedule_expr.startswith("every"):
                # Parse "every X minutes/hours"
                parts = schedule_expr.split()
                if len(parts) >= 3:
                    interval = int(parts[1])
                    unit = parts[2]
                    
                    if unit.startswith("minute"):
                        schedule.every(interval).minutes.do(
                            self._run_task_wrapper, task.id
                        ).tag(task.id)
                    elif unit.startswith("hour"):
                        schedule.every(interval).hours.do(
                            self._run_task_wrapper, task.id
                        ).tag(task.id)
            else:
                # For cron expressions, we'd need a more sophisticated parser
                # For now, default to daily
                self.logger.warning(f"Unsupported schedule expression: {schedule_expr}, defaulting to daily")
                schedule.every().day.at("02:00").do(
                    self._run_task_wrapper, task.id
                ).tag(task.id)
            
            self.logger.info(f"Scheduled task: {task.name} ({schedule_expr})")
            
        except Exception as e:
            self.logger.error(f"Failed to schedule task {task.name}: {e}")
    
    def _run_task_wrapper(self, task_id: str):
        """Wrapper to run task in thread pool"""
        asyncio.run(self._run_task(task_id))
    
    async def _run_task(self, task_id: str):
        """Execute a scheduled task"""
        if task_id not in self.tasks:
            self.logger.error(f"Task not found: {task_id}")
            return
        
        task = self.tasks[task_id]
        
        if not task.is_active:
            self.logger.info(f"Skipping inactive task: {task.name}")
            return
        
        self.logger.info(f"Running task: {task.name} ({task.task_type})")
        
        start_time = datetime.now()
        success = False
        error_message = None
        
        try:
            if task.task_type == 'webcrawl':
                success = await self._run_webcrawl_task(task)
            elif task.task_type == 'data_process':
                success = await self._run_data_processing_task(task)
            elif task.task_type == 'llm_analysis':
                success = await self._run_llm_analysis_task(task)
            elif task.task_type == 'report_gen':
                success = await self._run_report_generation_task(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
        except Exception as e:
            error_message = str(e)
            task.error_count += 1
            task.last_error = error_message
            self.logger.error(f"Task failed: {task.name} - {error_message}")
        
        # Update task status
        task.last_run = start_time
        task.run_count += 1
        
        if success:
            self.logger.info(f"Task completed successfully: {task.name}")
        
        self.save_tasks()
    
    async def _run_webcrawl_task(self, task: ScheduledTask) -> bool:
        """Execute a web crawling task"""
        config = task.config
        target_url = config.get('target_url')
        
        if not target_url:
            raise ValueError("No target_url specified in webcrawl config")
        
        # Create and run crawling job
        job_id = await self.scoup_manager.create_job(
            job_name=task.name,
            target_url=target_url,
            job_type=config.get('job_type', 'content_scraping'),
            config=config.get('scrape_config', {}),
            schedule=task.schedule_expression
        )
        
        result = await self.scoup_manager.run_job(job_id)
        return result.get('success', False)
    
    async def _run_data_processing_task(self, task: ScheduledTask) -> bool:
        """Execute a data processing task"""
        config = task.config
        
        # Process data from datalake
        input_path = config.get('input_path', 'datalake/scraped_data')
        output_path = config.get('output_path', 'datalake/processed_data')
        processing_type = config.get('processing_type', 'cleanup')
        
        result = await self.llm_processor.process_batch(
            input_path=input_path,
            output_path=output_path,
            processing_type=processing_type,
            config=config
        )
        
        return result.get('success', False)
    
    async def _run_llm_analysis_task(self, task: ScheduledTask) -> bool:
        """Execute an LLM analysis task"""
        config = task.config
        
        # Analyze data using LLM
        data_source = config.get('data_source', 'scraped_data')
        analysis_type = config.get('analysis_type', 'content_analysis')
        
        result = await self.llm_processor.analyze_data(
            data_source=data_source,
            analysis_type=analysis_type,
            config=config
        )
        
        return result.get('success', False)
    
    async def _run_report_generation_task(self, task: ScheduledTask) -> bool:
        """Execute a report generation task"""
        config = task.config
        
        # Generate reports
        report_type = config.get('report_type', 'usage_summary')
        output_format = config.get('output_format', 'pdf')
        
        # This would integrate with a reporting system
        self.logger.info(f"Generating {report_type} report in {output_format} format")
        
        # Mock successful report generation
        return True
    
    def start(self):
        """Start the scheduler"""
        self.running = True
        self.logger.info("Automation scheduler started")
        
        # Schedule all active tasks
        for task in self.tasks.values():
            if task.is_active:
                self._schedule_task(task)
        
        # Run scheduler loop
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        self.executor.shutdown(wait=True)
        self.logger.info("Automation scheduler stopped")
    
    def get_task_status(self) -> List[Dict[str, Any]]:
        """Get status of all tasks"""
        status = []
        
        for task in self.tasks.values():
            task_status = {
                'id': task.id,
                'name': task.name,
                'task_type': task.task_type,
                'is_active': task.is_active,
                'schedule': task.schedule_expression,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'run_count': task.run_count,
                'error_count': task.error_count,
                'last_error': task.last_error
            }
            status.append(task_status)
        
        return status


# =============================================================================
# PREDEFINED AUTOMATION TASKS
# =============================================================================

def create_default_tasks(scheduler: AutomationScheduler):
    """Create default automation tasks"""
    
    # Daily competitor analysis
    scheduler.add_task(
        task_id="competitor_analysis_daily",
        name="Daily Competitor Analysis",
        task_type="webcrawl",
        schedule_expression="daily",
        config={
            "target_url": "https://example-competitor.com",
            "job_type": "competitor_analysis",
            "scrape_config": {
                "extract_pricing": True,
                "extract_features": True,
                "extract_content": True,
                "screenshot": True
            }
        }
    )
    
    # Weekly market research
    scheduler.add_task(
        task_id="market_research_weekly",
        name="Weekly Market Research",
        task_type="webcrawl",
        schedule_expression="weekly",
        config={
            "target_url": "https://industry-news-site.com",
            "job_type": "market_research",
            "scrape_config": {
                "extract_articles": True,
                "extract_trends": True,
                "follow_links": True
            }
        }
    )
    
    # Hourly data processing
    scheduler.add_task(
        task_id="data_processing_hourly",
        name="Hourly Data Processing",
        task_type="data_process",
        schedule_expression="hourly",
        config={
            "input_path": "datalake/scraped_data",
            "output_path": "datalake/processed_data",
            "processing_type": "cleanup_and_normalize"
        }
    )
    
    # Daily LLM usage analysis
    scheduler.add_task(
        task_id="llm_analysis_daily",
        name="Daily LLM Usage Analysis",
        task_type="llm_analysis",
        schedule_expression="daily",
        config={
            "data_source": "llm_usage_stats",
            "analysis_type": "usage_patterns",
            "generate_insights": True
        }
    )
    
    # Weekly reports
    scheduler.add_task(
        task_id="weekly_reports",
        name="Weekly Business Reports",
        task_type="report_gen",
        schedule_expression="weekly",
        config={
            "report_type": "business_summary",
            "output_format": "pdf",
            "email_recipients": ["admin@agentshop.com"],
            "include_charts": True
        }
    )


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main function for testing the scheduler"""
    scheduler = AutomationScheduler()
    
    # Create default tasks if none exist
    if not scheduler.tasks:
        create_default_tasks(scheduler)
    
    # Show current tasks
    print("📋 Scheduled Tasks:")
    print("=" * 50)
    
    status = scheduler.get_task_status()
    for task in status:
        status_icon = "✅" if task['is_active'] else "⏸️"
        print(f"{status_icon} {task['name']}")
        print(f"   Type: {task['task_type']}")
        print(f"   Schedule: {task['schedule']}")
        print(f"   Runs: {task['run_count']}, Errors: {task['error_count']}")
        if task['last_run']:
            print(f"   Last Run: {task['last_run']}")
        print()
    
    print("Use Ctrl+C to stop the scheduler")
    
    # Start scheduler (this will run indefinitely)
    # scheduler.start()


if __name__ == "__main__":
    asyncio.run(main())