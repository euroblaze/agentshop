#!/usr/bin/env python3
"""
Email Notifier - Send email notifications for automation events
Supports SMTP, templates, and various notification types
"""

import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import aiosmtplib
import asyncio


@dataclass
class EmailConfig:
    """Email configuration"""
    smtp_host: str
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    use_ssl: bool = False
    from_email: str = ""
    from_name: str = "AgentShop Automation"


@dataclass
class EmailMessage:
    """Email message structure"""
    to_emails: List[str]
    subject: str
    html_content: str = ""
    text_content: str = ""
    cc_emails: List[str] = None
    bcc_emails: List[str] = None
    attachments: List[str] = None
    reply_to: str = ""


class EmailNotifier:
    """Handles email notifications for automation events"""
    
    def __init__(self, config: EmailConfig = None):
        self.config = config or self._load_config_from_env()
        self.templates = self._load_templates()
    
    def _load_config_from_env(self) -> EmailConfig:
        """Load email configuration from environment variables"""
        return EmailConfig(
            smtp_host=os.getenv('NOTIFICATION_EMAIL_SMTP_HOST', 'localhost'),
            smtp_port=int(os.getenv('NOTIFICATION_EMAIL_SMTP_PORT', '587')),
            username=os.getenv('NOTIFICATION_EMAIL_USER', ''),
            password=os.getenv('NOTIFICATION_EMAIL_PASS', ''),
            use_tls=os.getenv('NOTIFICATION_EMAIL_USE_TLS', 'true').lower() == 'true',
            from_email=os.getenv('NOTIFICATION_EMAIL_FROM', ''),
            from_name=os.getenv('NOTIFICATION_EMAIL_FROM_NAME', 'AgentShop Automation')
        )
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load email templates"""
        templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        templates = {}
        
        if os.path.exists(templates_dir):
            for filename in os.listdir(templates_dir):
                if filename.endswith('.json'):
                    template_name = filename.replace('.json', '')
                    with open(os.path.join(templates_dir, filename), 'r') as f:
                        templates[template_name] = json.load(f)
        
        # Default templates if none loaded
        if not templates:
            templates = self._get_default_templates()
        
        return templates
    
    def _get_default_templates(self) -> Dict[str, Dict[str, str]]:
        """Get default email templates"""
        return {
            'automation_success': {
                'subject': '✅ Automation Task Completed: {task_name}',
                'html': '''
                <h2>Automation Task Completed Successfully</h2>
                <p><strong>Task:</strong> {task_name}</p>
                <p><strong>Type:</strong> {task_type}</p>
                <p><strong>Completed at:</strong> {completed_at}</p>
                <p><strong>Items processed:</strong> {items_processed}</p>
                {summary}
                <hr>
                <p><em>AgentShop Automation System</em></p>
                ''',
                'text': '''
Automation Task Completed Successfully

Task: {task_name}
Type: {task_type}  
Completed at: {completed_at}
Items processed: {items_processed}

{summary}

--
AgentShop Automation System
                '''
            },
            'automation_error': {
                'subject': '❌ Automation Task Failed: {task_name}',
                'html': '''
                <h2>Automation Task Failed</h2>
                <p><strong>Task:</strong> {task_name}</p>
                <p><strong>Type:</strong> {task_type}</p>
                <p><strong>Failed at:</strong> {failed_at}</p>
                <p><strong>Error:</strong> <code>{error_message}</code></p>
                <p><strong>Retry count:</strong> {retry_count}</p>
                <hr>
                <p><em>Please investigate and resolve the issue.</em></p>
                <p><em>AgentShop Automation System</em></p>
                ''',
                'text': '''
Automation Task Failed

Task: {task_name}
Type: {task_type}
Failed at: {failed_at}
Error: {error_message}
Retry count: {retry_count}

Please investigate and resolve the issue.

--
AgentShop Automation System
                '''
            },
            'weekly_report': {
                'subject': '📊 Weekly Automation Report - {week_ending}',
                'html': '''
                <h2>Weekly Automation Report</h2>
                <p><strong>Week ending:</strong> {week_ending}</p>
                
                <h3>Summary</h3>
                <ul>
                    <li>Total tasks executed: {total_tasks}</li>
                    <li>Successful: {successful_tasks}</li>
                    <li>Failed: {failed_tasks}</li>
                    <li>Success rate: {success_rate}%</li>
                </ul>
                
                <h3>Top Performing Tasks</h3>
                {top_tasks}
                
                <h3>Issues Requiring Attention</h3>
                {issues}
                
                <hr>
                <p><em>AgentShop Automation System</em></p>
                ''',
                'text': '''
Weekly Automation Report

Week ending: {week_ending}

Summary:
- Total tasks executed: {total_tasks}
- Successful: {successful_tasks}  
- Failed: {failed_tasks}
- Success rate: {success_rate}%

Top Performing Tasks:
{top_tasks}

Issues Requiring Attention:
{issues}

--
AgentShop Automation System
                '''
            },
            'data_analysis_complete': {
                'subject': '🧠 Data Analysis Complete: {analysis_type}',
                'html': '''
                <h2>Data Analysis Completed</h2>
                <p><strong>Analysis type:</strong> {analysis_type}</p>
                <p><strong>Completed at:</strong> {completed_at}</p>
                <p><strong>Items analyzed:</strong> {items_analyzed}</p>
                
                <h3>Key Insights</h3>
                {insights}
                
                <h3>Summary</h3>
                <p>{summary}</p>
                
                <p><strong>Output file:</strong> {output_file}</p>
                
                <hr>
                <p><em>AgentShop Data Processing System</em></p>
                ''',
                'text': '''
Data Analysis Completed

Analysis type: {analysis_type}
Completed at: {completed_at}
Items analyzed: {items_analyzed}

Key Insights:
{insights}

Summary: {summary}

Output file: {output_file}

--
AgentShop Data Processing System
                '''
            }
        }
    
    async def send_email(self, message: EmailMessage) -> bool:
        """Send an email message asynchronously"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = ', '.join(message.to_emails)
            
            if message.cc_emails:
                msg['Cc'] = ', '.join(message.cc_emails)
            
            if message.reply_to:
                msg['Reply-To'] = message.reply_to
            
            # Add text content
            if message.text_content:
                text_part = MIMEText(message.text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            if message.html_content:
                html_part = MIMEText(message.html_content, 'html')
                msg.attach(html_part)
            
            # Add attachments
            if message.attachments:
                for file_path in message.attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)
            
            # Send email
            if self.config.use_ssl:
                await aiosmtplib.send(
                    msg,
                    hostname=self.config.smtp_host,
                    port=self.config.smtp_port,
                    username=self.config.username,
                    password=self.config.password,
                    use_tls=False,
                    start_tls=False
                )
            else:
                await aiosmtplib.send(
                    msg,
                    hostname=self.config.smtp_host,
                    port=self.config.smtp_port,
                    username=self.config.username,
                    password=self.config.password,
                    use_tls=self.config.use_tls
                )
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def send_email_sync(self, message: EmailMessage) -> bool:
        """Send an email message synchronously"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = ', '.join(message.to_emails)
            
            if message.cc_emails:
                msg['Cc'] = ', '.join(message.cc_emails)
            
            # Add content
            if message.text_content:
                text_part = MIMEText(message.text_content, 'plain')
                msg.attach(text_part)
            
            if message.html_content:
                html_part = MIMEText(message.html_content, 'html')
                msg.attach(html_part)
            
            # Connect and send
            if self.config.use_ssl:
                server = smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port)
            else:
                server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
                if self.config.use_tls:
                    server.starttls()
            
            if self.config.username and self.config.password:
                server.login(self.config.username, self.config.password)
            
            # Send to all recipients
            recipients = message.to_emails[:]
            if message.cc_emails:
                recipients.extend(message.cc_emails)
            if message.bcc_emails:
                recipients.extend(message.bcc_emails)
            
            server.send_message(msg, to_addrs=recipients)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def notify_automation_success(
        self,
        task_name: str,
        task_type: str,
        items_processed: int,
        summary: str = "",
        recipients: List[str] = None
    ) -> bool:
        """Send notification for successful automation task"""
        
        template = self.templates.get('automation_success', {})
        
        variables = {
            'task_name': task_name,
            'task_type': task_type,
            'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items_processed': items_processed,
            'summary': summary
        }
        
        message = EmailMessage(
            to_emails=recipients or [self.config.from_email],
            subject=template.get('subject', '').format(**variables),
            html_content=template.get('html', '').format(**variables),
            text_content=template.get('text', '').format(**variables)
        )
        
        return self.send_email_sync(message)
    
    def notify_automation_error(
        self,
        task_name: str,
        task_type: str,
        error_message: str,
        retry_count: int = 0,
        recipients: List[str] = None
    ) -> bool:
        """Send notification for failed automation task"""
        
        template = self.templates.get('automation_error', {})
        
        variables = {
            'task_name': task_name,
            'task_type': task_type,
            'failed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': error_message,
            'retry_count': retry_count
        }
        
        message = EmailMessage(
            to_emails=recipients or [self.config.from_email],
            subject=template.get('subject', '').format(**variables),
            html_content=template.get('html', '').format(**variables),
            text_content=template.get('text', '').format(**variables)
        )
        
        return self.send_email_sync(message)
    
    def send_weekly_report(
        self,
        report_data: Dict[str, Any],
        recipients: List[str] = None
    ) -> bool:
        """Send weekly automation report"""
        
        template = self.templates.get('weekly_report', {})
        
        # Format top tasks
        top_tasks = ""
        for task in report_data.get('top_tasks', []):
            top_tasks += f"- {task['name']}: {task['success_rate']}% success rate\n"
        
        # Format issues
        issues = ""
        for issue in report_data.get('issues', []):
            issues += f"- {issue['task']}: {issue['description']}\n"
        
        variables = {
            'week_ending': report_data.get('week_ending', datetime.now().strftime('%Y-%m-%d')),
            'total_tasks': report_data.get('total_tasks', 0),
            'successful_tasks': report_data.get('successful_tasks', 0),
            'failed_tasks': report_data.get('failed_tasks', 0),
            'success_rate': report_data.get('success_rate', 0),
            'top_tasks': top_tasks,
            'issues': issues or "No issues to report"
        }
        
        message = EmailMessage(
            to_emails=recipients or [self.config.from_email],
            subject=template.get('subject', '').format(**variables),
            html_content=template.get('html', '').format(**variables),
            text_content=template.get('text', '').format(**variables)
        )
        
        return self.send_email_sync(message)
    
    def notify_data_analysis_complete(
        self,
        analysis_type: str,
        items_analyzed: int,
        insights: List[str],
        summary: str,
        output_file: str = "",
        recipients: List[str] = None
    ) -> bool:
        """Send notification for completed data analysis"""
        
        template = self.templates.get('data_analysis_complete', {})
        
        # Format insights
        insights_text = ""
        for insight in insights:
            insights_text += f"• {insight}\n"
        
        variables = {
            'analysis_type': analysis_type,
            'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items_analyzed': items_analyzed,
            'insights': insights_text,
            'summary': summary,
            'output_file': output_file
        }
        
        message = EmailMessage(
            to_emails=recipients or [self.config.from_email],
            subject=template.get('subject', '').format(**variables),
            html_content=template.get('html', '').format(**variables),
            text_content=template.get('text', '').format(**variables),
            attachments=[output_file] if output_file and os.path.exists(output_file) else None
        )
        
        return self.send_email_sync(message)
    
    def test_email_config(self) -> bool:
        """Test email configuration by sending a test message"""
        
        test_message = EmailMessage(
            to_emails=[self.config.from_email],
            subject="AgentShop Email Configuration Test",
            html_content="""
            <h2>Email Configuration Test</h2>
            <p>This is a test email to verify your email configuration is working correctly.</p>
            <p><strong>Timestamp:</strong> {timestamp}</p>
            <hr>
            <p><em>AgentShop Automation System</em></p>
            """.format(timestamp=datetime.now().isoformat()),
            text_content=f"""
Email Configuration Test

This is a test email to verify your email configuration is working correctly.

Timestamp: {datetime.now().isoformat()}

--
AgentShop Automation System
            """
        )
        
        success = self.send_email_sync(test_message)
        
        if success:
            print("✅ Test email sent successfully!")
        else:
            print("❌ Failed to send test email. Please check your configuration.")
        
        return success


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def example_usage():
    """Example of how to use the email notifier"""
    
    # Initialize notifier (will load config from environment)
    notifier = EmailNotifier()
    
    # Test configuration
    print("Testing email configuration...")
    if not notifier.test_email_config():
        print("Email configuration test failed. Please check your settings.")
        return
    
    # Send success notification
    notifier.notify_automation_success(
        task_name="Daily Competitor Analysis",
        task_type="webcrawl",
        items_processed=25,
        summary="Successfully scraped 25 competitor product pages. Found 3 new products and 5 price changes.",
        recipients=["admin@agentshop.com"]
    )
    
    # Send error notification
    notifier.notify_automation_error(
        task_name="Market Research Crawler",
        task_type="webcrawl",
        error_message="HTTP 429: Rate limit exceeded",
        retry_count=3,
        recipients=["admin@agentshop.com"]
    )
    
    # Send data analysis notification
    notifier.notify_data_analysis_complete(
        analysis_type="Content Analysis",
        items_analyzed=100,
        insights=[
            "70% of articles mention AI automation trends",
            "Average sentiment score increased by 15%",
            "Top keywords: AI, automation, efficiency, cost-savings"
        ],
        summary="Analysis completed successfully with high confidence scores",
        output_file="datalake/processed_data/analysis_results.json",
        recipients=["data-team@agentshop.com"]
    )


if __name__ == "__main__":
    example_usage()