#!/usr/bin/env ts-node
/**
 * AgentShop CLI - TypeScript Management Interface
 * Provides command-line tools for managing the AgentShop platform
 */

import { Command } from 'commander';
import axios, { AxiosInstance } from 'axios';
import fs from 'fs';
import path from 'path';
import chalk from 'chalk';
import ora from 'ora';
import inquirer from 'inquirer';

interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  errors?: string[];
}

interface LLMProvider {
  provider: string;
  is_enabled: boolean;
  is_healthy: boolean;
  api_key_configured: boolean;
  default_model?: string;
  current_daily_cost: number;
  daily_cost_limit: number;
}

interface UsageStats {
  date: string;
  provider: string;
  model: string;
  request_count: number;
  successful_requests: number;
  total_cost: number;
  average_response_time_ms: number;
}

class AgentShopCLI {
  private api: AxiosInstance;
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:5000') {
    this.baseUrl = baseUrl;
    this.api = axios.create({
      baseURL: baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async checkConnection(): Promise<boolean> {
    try {
      await this.api.get('/health');
      return true;
    } catch {
      return false;
    }
  }

  async getProviders(): Promise<LLMProvider[]> {
    const response = await this.api.get<ApiResponse<LLMProvider[]>>('/api/llm/analytics/providers/status');
    return response.data.data;
  }

  async getUsageStats(days: number = 7, provider?: string): Promise<UsageStats[]> {
    const params = new URLSearchParams();
    params.append('days', days.toString());
    if (provider) params.append('provider', provider);

    const response = await this.api.get<ApiResponse<UsageStats[]>>(
      `/api/llm/analytics/usage?${params}`
    );
    return response.data.data;
  }

  async enableProvider(provider: string, apiKey: string, model?: string): Promise<void> {
    const payload: any = { api_key: apiKey };
    if (model) payload.default_model = model;

    await this.api.post(`/api/llm/config/providers/${provider}/enable`, payload);
  }

  async disableProvider(provider: string): Promise<void> {
    await this.api.post(`/api/llm/config/providers/${provider}/disable`);
  }

  async testGeneration(prompt: string, provider: string, model?: string): Promise<any> {
    const payload: any = {
      prompt,
      provider,
      max_tokens: 100,
    };
    if (model) payload.model = model;

    const response = await this.api.post('/api/llm/generate', payload);
    return response.data.data;
  }

  async healthCheck(): Promise<Record<string, boolean>> {
    const response = await this.api.get<ApiResponse<Record<string, boolean>>>(
      '/api/llm/analytics/health'
    );
    return response.data.data;
  }
}

// =============================================================================
// CLI SETUP
// =============================================================================

const program = new Command();
const cli = new AgentShopCLI();

program
  .name('agentshop')
  .description('AgentShop CLI - Manage your AI Agent Marketplace')
  .version('1.0.0')
  .option('-u, --url <url>', 'API base URL', 'http://localhost:5000');

// =============================================================================
// LLM COMMANDS
// =============================================================================

const llmCommand = program.command('llm').description('LLM provider management');

llmCommand
  .command('providers')
  .description('List all LLM providers and their status')
  .action(async () => {
    const spinner = ora('Fetching providers...').start();
    
    try {
      const connected = await cli.checkConnection();
      if (!connected) {
        spinner.fail('Cannot connect to AgentShop API. Is the server running?');
        process.exit(1);
      }

      const providers = await cli.getProviders();
      spinner.stop();

      console.log(chalk.blue.bold('\n🤖 LLM Providers Status'));
      console.log('='.repeat(50));

      if (providers.length === 0) {
        console.log(chalk.yellow('No providers configured.'));
        return;
      }

      for (const provider of providers) {
        const statusIcon = provider.is_healthy ? '✅' : '❌';
        const enabledIcon = provider.is_enabled ? '🟢' : '🔴';
        
        console.log(`${statusIcon} ${enabledIcon} ${chalk.bold(provider.provider.toUpperCase())}`);
        console.log(`   Enabled: ${provider.is_enabled ? chalk.green('Yes') : chalk.red('No')}`);
        console.log(`   Healthy: ${provider.is_healthy ? chalk.green('Yes') : chalk.red('No')}`);
        console.log(`   API Key: ${provider.api_key_configured ? '✅' : '❌'}`);
        console.log(`   Default Model: ${provider.default_model || 'Not set'}`);
        console.log(
          `   Daily Cost: $${provider.current_daily_cost.toFixed(4)} / $${provider.daily_cost_limit.toFixed(2)}`
        );
        console.log();
      }
    } catch (error: any) {
      spinner.fail(`Error: ${error.message}`);
    }
  });

llmCommand
  .command('enable <provider> <api-key>')
  .description('Enable an LLM provider')
  .option('-m, --model <model>', 'Default model for the provider')
  .action(async (provider: string, apiKey: string, options: any) => {
    const spinner = ora(`Enabling ${provider.toUpperCase()} provider...`).start();
    
    try {
      await cli.enableProvider(provider, apiKey, options.model);
      spinner.succeed(`${provider.toUpperCase()} provider enabled successfully!`);
      
      if (options.model) {
        console.log(`   Default model: ${options.model}`);
      }
    } catch (error: any) {
      spinner.fail(`Error enabling provider: ${error.message}`);
    }
  });

llmCommand
  .command('disable <provider>')
  .description('Disable an LLM provider')
  .action(async (provider: string) => {
    const spinner = ora(`Disabling ${provider.toUpperCase()} provider...`).start();
    
    try {
      await cli.disableProvider(provider);
      spinner.succeed(`${provider.toUpperCase()} provider disabled successfully!`);
    } catch (error: any) {
      spinner.fail(`Error disabling provider: ${error.message}`);
    }
  });

llmCommand
  .command('stats')
  .description('Show LLM usage statistics')
  .option('-d, --days <days>', 'Number of days to show stats for', '7')
  .option('-p, --provider <provider>', 'Filter by specific provider')
  .action(async (options: any) => {
    const spinner = ora('Fetching statistics...').start();
    
    try {
      const stats = await cli.getUsageStats(parseInt(options.days), options.provider);
      spinner.stop();

      console.log(chalk.blue.bold(`\n📊 LLM Usage Statistics (Last ${options.days} days)`));
      console.log('='.repeat(60));

      if (stats.length === 0) {
        console.log(chalk.yellow('No usage data found.'));
        return;
      }

      const totalRequests = stats.reduce((sum, s) => sum + s.request_count, 0);
      const totalCost = stats.reduce((sum, s) => sum + s.total_cost, 0);

      console.log(chalk.green.bold('📈 Summary:'));
      console.log(`   Total Requests: ${chalk.cyan(totalRequests.toLocaleString())}`);
      console.log(`   Total Cost: ${chalk.green('$' + totalCost.toFixed(4))}`);
      console.log();

      // Group by provider
      const providerStats: Record<string, any> = {};
      for (const stat of stats) {
        if (!providerStats[stat.provider]) {
          providerStats[stat.provider] = { requests: 0, cost: 0 };
        }
        providerStats[stat.provider].requests += stat.request_count;
        providerStats[stat.provider].cost += stat.total_cost;
      }

      console.log(chalk.blue.bold('🤖 By Provider:'));
      for (const [provider, data] of Object.entries(providerStats)) {
        console.log(`   ${chalk.bold(provider.toUpperCase())}:`);
        console.log(`     Requests: ${chalk.cyan(data.requests.toLocaleString())}`);
        console.log(`     Cost: ${chalk.green('$' + data.cost.toFixed(4))}`);
        console.log();
      }
    } catch (error: any) {
      spinner.fail(`Error: ${error.message}`);
    }
  });

llmCommand
  .command('test <prompt>')
  .description('Test LLM generation')
  .option('-p, --provider <provider>', 'LLM provider to use', 'openai')
  .option('-m, --model <model>', 'Model to use')
  .action(async (prompt: string, options: any) => {
    const spinner = ora(`Testing ${options.provider.toUpperCase()} provider...`).start();
    
    try {
      const result = await cli.testGeneration(prompt, options.provider, options.model);
      spinner.stop();

      console.log(chalk.blue.bold(`\n🧪 Test Results`));
      console.log('='.repeat(50));
      console.log(chalk.bold('Prompt:'), prompt);
      console.log();
      console.log(chalk.green.bold('✅ Response:'));
      console.log(result.content);
      console.log();
      console.log(chalk.blue.bold('📊 Stats:'));
      console.log(`   Provider: ${result.provider}`);
      console.log(`   Model: ${result.model}`);
      console.log(`   Tokens: ${result.tokens_used}`);
      console.log(`   Cost: $${result.cost.toFixed(6)}`);
      console.log(`   Time: ${result.processing_time_ms}ms`);
      console.log(`   Cached: ${result.cached ? 'Yes' : 'No'}`);
    } catch (error: any) {
      spinner.fail(`Test failed: ${error.message}`);
    }
  });

llmCommand
  .command('health')
  .description('Check health of all LLM providers')
  .action(async () => {
    const spinner = ora('Checking provider health...').start();
    
    try {
      const health = await cli.healthCheck();
      spinner.stop();

      console.log(chalk.blue.bold('\n🏥 LLM Provider Health Check'));
      console.log('='.repeat(50));

      for (const [provider, healthy] of Object.entries(health)) {
        const icon = healthy ? '✅' : '❌';
        const status = healthy ? chalk.green('Healthy') : chalk.red('Unhealthy');
        console.log(`${icon} ${chalk.bold(provider.toUpperCase())}: ${status}`);
      }
    } catch (error: any) {
      spinner.fail(`Health check failed: ${error.message}`);
    }
  });

// =============================================================================
// DATA COMMANDS
// =============================================================================

const dataCommand = program.command('data').description('Data management commands');

dataCommand
  .command('export')
  .description('Export usage data')
  .option('-f, --format <format>', 'Export format (json|csv)', 'json')
  .option('-o, --output <file>', 'Output file path')
  .option('-d, --days <days>', 'Number of days to export', '30')
  .action(async (options: any) => {
    const spinner = ora('Exporting data...').start();
    
    try {
      const stats = await cli.getUsageStats(parseInt(options.days));
      
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
      const defaultOutput = `./datalake/processed_data/export_${timestamp}.${options.format}`;
      const outputPath = options.output || defaultOutput;
      
      // Ensure directory exists
      const dir = path.dirname(outputPath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      if (options.format === 'json') {
        fs.writeFileSync(outputPath, JSON.stringify(stats, null, 2));
      } else if (options.format === 'csv') {
        const csv = convertToCSV(stats);
        fs.writeFileSync(outputPath, csv);
      }

      spinner.succeed(`Data exported to: ${outputPath}`);
    } catch (error: any) {
      spinner.fail(`Export failed: ${error.message}`);
    }
  });

// =============================================================================
// INTERACTIVE COMMANDS
// =============================================================================

program
  .command('setup')
  .description('Interactive setup wizard')
  .action(async () => {
    console.log(chalk.blue.bold('\n🚀 AgentShop Setup Wizard'));
    console.log('='.repeat(50));

    try {
      const connected = await cli.checkConnection();
      if (!connected) {
        console.log(chalk.red('❌ Cannot connect to AgentShop API. Please start the server first.'));
        process.exit(1);
      }

      const answers = await inquirer.prompt([
        {
          type: 'checkbox',
          name: 'providers',
          message: 'Which LLM providers would you like to enable?',
          choices: [
            { name: 'OpenAI (GPT models)', value: 'openai' },
            { name: 'Anthropic Claude', value: 'claude' },
            { name: 'Groq (Fast inference)', value: 'groq' },
            { name: 'Perplexity (Search-augmented)', value: 'perplexity' },
            { name: 'Ollama (Local models)', value: 'ollama' },
          ],
        },
      ]);

      for (const provider of answers.providers) {
        if (provider === 'ollama') {
          const ollamaConfig = await inquirer.prompt([
            {
              type: 'input',
              name: 'baseUrl',
              message: 'Ollama base URL:',
              default: 'http://localhost:11434',
            },
          ]);
          
          console.log(chalk.green(`✅ Ollama configured with URL: ${ollamaConfig.baseUrl}`));
        } else {
          const providerConfig = await inquirer.prompt([
            {
              type: 'password',
              name: 'apiKey',
              message: `Enter ${provider.toUpperCase()} API key:`,
              mask: '*',
            },
            {
              type: 'input',
              name: 'model',
              message: `Default model for ${provider} (optional):`,
            },
          ]);

          const spinner = ora(`Configuring ${provider.toUpperCase()}...`).start();
          
          try {
            await cli.enableProvider(provider, providerConfig.apiKey, providerConfig.model);
            spinner.succeed(`${provider.toUpperCase()} configured successfully!`);
          } catch (error: any) {
            spinner.fail(`Failed to configure ${provider}: ${error.message}`);
          }
        }
      }

      console.log(chalk.green.bold('\n🎉 Setup completed!'));
      console.log('You can now use the AgentShop CLI and web interface.');
    } catch (error: any) {
      console.log(chalk.red(`Setup failed: ${error.message}`));
    }
  });

program
  .command('status')
  .description('Show system status')
  .action(async () => {
    console.log(chalk.blue.bold('\n🏥 AgentShop System Status'));
    console.log('='.repeat(50));

    const spinner = ora('Checking system status...').start();
    
    try {
      const connected = await cli.checkConnection();
      spinner.stop();

      if (connected) {
        console.log(`✅ API Server: ${chalk.green('Connected')} (${cli.baseUrl})`);
        
        // Check LLM providers
        const health = await cli.healthCheck();
        console.log('\n🤖 LLM Providers:');
        
        for (const [provider, healthy] of Object.entries(health)) {
          const icon = healthy ? '✅' : '❌';
          console.log(`   ${icon} ${provider.toUpperCase()}`);
        }
      } else {
        console.log(`❌ API Server: ${chalk.red('Disconnected')}`);
        console.log(chalk.yellow('Please ensure the backend server is running.'));
      }
    } catch (error: any) {
      spinner.fail(`Status check failed: ${error.message}`);
    }
  });

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function convertToCSV(data: any[]): string {
  if (data.length === 0) return '';
  
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header];
        return typeof value === 'string' && value.includes(',') 
          ? `"${value}"` 
          : value;
      }).join(',')
    )
  ].join('\n');
  
  return csvContent;
}

// =============================================================================
// MAIN EXECUTION
// =============================================================================

async function main() {
  try {
    await program.parseAsync(process.argv);
  } catch (error: any) {
    console.error(chalk.red(`❌ Error: ${error.message}`));
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

export { AgentShopCLI };