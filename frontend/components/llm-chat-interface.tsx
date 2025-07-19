import React, { useState, useRef, useEffect } from 'react';
import { LLMApiClient, ChatMessage, ChatResponse, Conversation } from '../services/llm-api-client';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  provider?: string;
  model?: string;
  cost?: number;
  tokens?: number;
  request_id?: number;
}

interface ChatInterfaceProps {
  apiClient: LLMApiClient;
  sessionId: string;
  userId?: number;
  defaultProvider?: string;
  defaultModel?: string;
  onCostUpdate?: (totalCost: number) => void;
  systemPrompt?: string;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  apiClient,
  sessionId,
  userId,
  defaultProvider = 'openai',
  defaultModel,
  onCostUpdate,
  systemPrompt
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentProvider, setCurrentProvider] = useState(defaultProvider);
  const [currentModel, setCurrentModel] = useState(defaultModel || '');
  const [providers, setProviders] = useState<string[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [totalCost, setTotalCost] = useState(0);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    loadProviders();
    loadChatHistory();
  }, []);

  useEffect(() => {
    if (currentProvider) {
      loadModels(currentProvider);
    }
  }, [currentProvider]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (onCostUpdate) {
      onCostUpdate(totalCost);
    }
  }, [totalCost, onCostUpdate]);

  const loadProviders = async () => {
    try {
      const providerList = await apiClient.getProviders();
      setProviders(providerList);
    } catch (error) {
      console.error('Failed to load providers:', error);
    }
  };

  const loadModels = async (provider: string) => {
    try {
      const modelList = await apiClient.getModels(provider);
      setModels(modelList);
      if (modelList.length > 0 && !currentModel) {
        setCurrentModel(modelList[0]);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
      setModels([]);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = async () => {
    try {
      const history = await apiClient.getChatHistory(sessionId);
      if (history.messages && history.messages.length > 0) {
        const loadedMessages: Message[] = history.messages.map((msg, index) => ({
          id: `${index}-${msg.role}`,
          content: msg.content,
          sender: msg.role as 'user' | 'assistant',
          timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
          provider: msg.provider,
          model: msg.model,
          cost: msg.cost,
          tokens: msg.tokens_used,
          request_id: msg.request_id
        }));
        setMessages(loadedMessages);
        
        // Calculate total cost from loaded messages
        const totalCostFromHistory = loadedMessages.reduce((sum, msg) => sum + (msg.cost || 0), 0);
        setTotalCost(totalCostFromHistory);
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const messageText = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      const context: Record<string, any> = {};
      if (systemPrompt) {
        context.system_prompt = systemPrompt;
      }

      const response: ChatResponse = await apiClient.sendChatMessage(
        messageText,
        sessionId,
        {
          provider: currentProvider,
          model: currentModel,
          user_id: userId,
          context
        }
      );

      const assistantMessage: Message = {
        id: response.assistant_message_id.toString(),
        content: response.content,
        sender: 'assistant',
        timestamp: new Date(),
        provider: response.provider,
        model: response.model,
        cost: response.cost,
        tokens: response.tokens_used,
        request_id: response.request_id
      };

      setMessages(prev => [...prev, assistantMessage]);
      setTotalCost(prev => prev + response.cost);

    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setTotalCost(0);
    // Note: This only clears the UI. The backend conversation history remains intact.
    // To actually clear the conversation, you would need to implement a backend endpoint.
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="provider-selector">
          <label>Provider:</label>
          <select
            value={currentProvider}
            onChange={(e) => setCurrentProvider(e.target.value)}
            disabled={isLoading}
          >
            {providers.map(provider => (
              <option key={provider} value={provider}>
                {provider.charAt(0).toUpperCase() + provider.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className="model-selector">
          <label>Model:</label>
          <select
            value={currentModel}
            onChange={(e) => setCurrentModel(e.target.value)}
            disabled={isLoading}
          >
            {models.map(model => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </div>

        <div className="cost-display">
          Total Cost: ${totalCost.toFixed(4)}
        </div>

        <button onClick={clearChat} className="clear-button">
          Clear Chat
        </button>
      </div>

      <div className="messages-container">
        {messages.map(message => (
          <div key={message.id} className={`message ${message.sender}`}>
            <div className="message-content">
              {message.content}
            </div>
            <div className="message-meta">
              <span className="timestamp">
                {message.timestamp.toLocaleTimeString()}
              </span>
              {message.provider && (
                <span className="provider">
                  {message.provider} ({message.model})
                </span>
              )}
              {message.cost !== undefined && (
                <span className="cost">
                  ${message.cost.toFixed(4)}
                </span>
              )}
              {message.tokens && (
                <span className="tokens">
                  {message.tokens} tokens
                </span>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message assistant loading">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <textarea
          ref={inputRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={isLoading}
          rows={3}
        />
        <button type="submit" disabled={isLoading || !inputValue.trim()}>
          Send
        </button>
      </form>
    </div>
  );
};