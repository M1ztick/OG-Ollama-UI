/**
 * Home page component - Enhanced Ollama chat interface with streaming and model selection
 */
import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Copy, Trash2, ChevronDown, Zap } from 'lucide-react'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Card } from '../components/ui/card'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu'

interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  isStreaming?: boolean
}

interface OllamaModel {
  name: string
  size: number
  modified_at: string
}

export default function HomePage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: "Hello! I'm your Ollama assistant. Send me a message to get started!",
      role: 'assistant',
      timestamp: new Date()
    }
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [availableModels, setAvailableModels] = useState<OllamaModel[]>([])
  const [selectedModel, setSelectedModel] = useState('llama3.2')
  const [isLoadingModels, setIsLoadingModels] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  /**
   * Scroll to bottom of messages
   */
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  /**
   * Fetch available models from Ollama
   */
  const fetchAvailableModels = async () => {
    try {
      const response = await fetch('http://localhost:11434/api/tags')
      if (response.ok) {
        const data = await response.json()
        setAvailableModels(data.models || [])
        
        // Set first model as default if current selection isn't available
        if (data.models && data.models.length > 0) {
          const modelNames = data.models.map((m: OllamaModel) => m.name)
          if (!modelNames.includes(selectedModel)) {
            setSelectedModel(data.models[0].name)
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch models:', error)
      // Set fallback models if API fails
      setAvailableModels([
        { name: 'llama3.2', size: 0, modified_at: new Date().toISOString() },
        { name: 'llama3', size: 0, modified_at: new Date().toISOString() }
      ])
    } finally {
      setIsLoadingModels(false)
    }
  }

  useEffect(() => {
    fetchAvailableModels()
  }, [])

  /**
   * Format model size for display
   */
  const formatModelSize = (size: number) => {
    if (size === 0) return 'Unknown size'
    const gb = size / (1024 * 1024 * 1024)
    return gb > 1 ? `${gb.toFixed(1)}GB` : `${(size / (1024 * 1024)).toFixed(0)}MB`
  }

  /**
   * Send message to Ollama with streaming
   */
  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      role: 'user',
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const currentInput = inputMessage
    setInputMessage('')
    setIsLoading(true)

    // Create assistant message placeholder
    const assistantMessageId = (Date.now() + 1).toString()
    const assistantMessage: Message = {
      id: assistantMessageId,
      content: '',
      role: 'assistant',
      timestamp: new Date(),
      isStreaming: true
    }

    setMessages(prev => [...prev, assistantMessage])

    // Create abort controller for this request
    abortControllerRef.current = new AbortController()

    try {
      const response = await fetch('http://localhost:11434/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: selectedModel,
          prompt: currentInput,
          stream: true
        }),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No reader available')
      }

      let accumulatedContent = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        const chunk = new TextDecoder().decode(value)
        const lines = chunk.split('\n').filter(line => line.trim())

        for (const line of lines) {
          try {
            const data = JSON.parse(line)
            
            if (data.response) {
              accumulatedContent += data.response
              
              // Update the assistant message with new content
              setMessages(prev => prev.map(msg => 
                msg.id === assistantMessageId 
                  ? { ...msg, content: accumulatedContent }
                  : msg
              ))
            }

            if (data.done) {
              // Mark streaming as complete
              setMessages(prev => prev.map(msg => 
                msg.id === assistantMessageId 
                  ? { ...msg, isStreaming: false }
                  : msg
              ))
              break
            }
          } catch (parseError) {
            console.warn('Failed to parse JSON:', line)
          }
        }
      }

    } catch (error) {
      console.error('Error calling Ollama:', error)
      
      if (error instanceof Error && error.name !== 'AbortError') {
        const errorMessage = `❌ Connection Error: ${error.message}. Is Ollama running with model '${selectedModel}'?`
        
        setMessages(prev => prev.map(msg => 
          msg.id === assistantMessageId 
            ? { ...msg, content: errorMessage, isStreaming: false }
            : msg
        ))
      }
    } finally {
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  /**
   * Copy message content to clipboard
   */
  const copyMessage = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  /**
   * Clear all messages
   */
  const clearMessages = () => {
    setMessages([
      {
        id: '1',
        content: `Hello! I'm your Ollama assistant running ${selectedModel}. Send me a message to get started!`,
        role: 'assistant',
        timestamp: new Date()
      }
    ])
  }

  /**
   * Stop current generation
   */
  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setIsLoading(false)
    }
  }

  /**
   * Handle model selection
   */
  const handleModelSelect = (modelName: string) => {
    setSelectedModel(modelName)
    
    // Add system message about model switch
    const systemMessage: Message = {
      id: Date.now().toString(),
      content: `🔄 Switched to model: ${modelName}`,
      role: 'assistant',
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, systemMessage])
  }

  /**
   * Handle Enter key press
   */
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
      {/* Header */}
      <div className="max-w-4xl mx-auto mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-white">
            <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
              <Bot className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Ollama Chat</h1>
              <p className="text-gray-300">Local AI Assistant • Streaming Mode</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Model Selector */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  className="bg-white/10 border-white/20 text-white hover:bg-white/20 min-w-[160px]"
                  disabled={isLoadingModels}
                >
                  <Zap className="w-4 h-4 mr-2" />
                  {isLoadingModels ? 'Loading...' : selectedModel}
                  <ChevronDown className="w-4 h-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-80 bg-slate-800 border-slate-700">
                {availableModels.length > 0 ? (
                  availableModels.map((model) => (
                    <DropdownMenuItem
                      key={model.name}
                      onClick={() => handleModelSelect(model.name)}
                      className="flex flex-col items-start py-3 text-white hover:bg-slate-700"
                    >
                      <div className="flex items-center justify-between w-full">
                        <span className="font-medium">{model.name}</span>
                        {model.name === selectedModel && (
                          <div className="w-2 h-2 bg-green-400 rounded-full" />
                        )}
                      </div>
                      <span className="text-xs text-gray-400">
                        {formatModelSize(model.size)} • {new Date(model.modified_at).toLocaleDateString()}
                      </span>
                    </DropdownMenuItem>
                  ))
                ) : (
                  <DropdownMenuItem disabled className="text-gray-400">
                    No models found
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Clear Button */}
            <Button
              onClick={clearMessages}
              variant="outline"
              size="sm"
              className="bg-transparent border-white/20 text-white hover:bg-white/10"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Clear
            </Button>
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <div className="max-w-4xl mx-auto">
        {/* Messages */}
        <div className="space-y-4 mb-6 max-h-[500px] overflow-y-auto scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent">
          {messages.map((message, index) => (
            <div
              key={message.id}
              className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-4 duration-300`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {message.role === 'assistant' && (
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-white" />
                </div>
              )}
              
              <div className="group relative max-w-lg">
                <Card className={`p-4 ${
                  message.role === 'user' 
                    ? 'bg-blue-600/20 border-blue-400/20' 
                    : 'bg-white/10 border-white/20'
                } backdrop-blur-lg transition-all duration-200 hover:bg-opacity-30`}>
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-white text-sm whitespace-pre-wrap flex-1">
                      {message.content}
                      {message.isStreaming && (
                        <span className="inline-block w-2 h-4 bg-white ml-1 animate-pulse" />
                      )}
                    </p>
                  </div>
                  
                  {/* Message timestamp */}
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/10">
                    <span className="text-xs text-gray-400">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                    
                    {/* Copy button */}
                    <Button
                      onClick={() => copyMessage(message.content)}
                      variant="ghost"
                      size="sm"
                      className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0 text-gray-400 hover:text-white"
                    >
                      <Copy className="w-3 h-3" />
                    </Button>
                  </div>
                </Card>
              </div>
              
              {message.role === 'user' && (
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center flex-shrink-0">
                  <User className="w-5 h-5 text-white" />
                </div>
              )}
            </div>
          ))}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <Card className="bg-white/10 border-white/20 backdrop-blur-lg p-4">
          <div className="flex gap-3">
            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={`Ask ${selectedModel} anything...`}
              className="flex-1 bg-transparent border-white/20 text-white placeholder-gray-400 focus:border-purple-400"
              disabled={isLoading}
            />
            
            {isLoading ? (
              <Button
                onClick={stopGeneration}
                className="bg-red-500 hover:bg-red-600 text-white px-4"
              >
                Stop
              </Button>
            ) : (
              <Button
                onClick={sendMessage}
                disabled={!inputMessage.trim()}
                className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white px-6"
              >
                <Send className="w-5 h-5" />
              </Button>
            )}
          </div>
          
          {isLoading && (
            <div className="mt-3 flex items-center gap-2 text-gray-300 text-sm">
              <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              <span>{selectedModel} is thinking...</span>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
