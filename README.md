# OG Ollama UI

A modern, responsive React-based user interface for [Ollama](https://ollama.ai/) with real-time streaming chat support.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![React](https://img.shields.io/badge/React-18.3.1-blue.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-latest-blue.svg)

## ✨ Features

- 🚀 **Real-time streaming** chat with Ollama models
- 🎨 **Modern UI** built with React, Tailwind CSS, and shadcn/ui
- 🔄 **Model switching** on-the-fly with model size information
- 📱 **Responsive design** that works on desktop and mobile
- 💾 **Message history** with copy functionality
- ⚡ **Fast build** system with esbuild
- 🎯 **Type-safe** development with TypeScript

## 🛠️ Tech Stack

### Frontend

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Beautiful, accessible components
- **React Router** - Client-side routing
- **Lucide React** - Beautiful icons

### Build System

- **esbuild** - Ultra-fast bundling
- **PostCSS** - CSS processing
- **Autoprefixer** - Vendor prefix automation

### Backend (Planned)

- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation
- **Multiple AI APIs** - Ollama, OpenAI, Perplexity support

## 🚀 Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/) (v16 or higher)
- [Ollama](https://ollama.ai/) installed and running
- At least one Ollama model installed (e.g., `ollama pull llama3.2`)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/M1ztick/OG-Ollama-UI.git
   cd OG-Ollama-UI
   ```

2. **Install dependencies**

   ```bash
   npm install
   ```

3. **Start Ollama** (if not already running)

   ```bash
   ollama serve
   ```

4. **Start the development server**

   ```bash
   npm run dev
   ```

5. **Open your browser** to the URL shown in the terminal (typically `http://localhost:8000`)

## 📖 Usage

1. **Select a Model**: Use the model dropdown to choose from your installed Ollama models
2. **Start Chatting**: Type your message and press Enter or click Send
3. **Real-time Responses**: Watch as the AI streams responses in real-time
4. **Copy Messages**: Hover over messages to copy them to clipboard
5. **Clear History**: Use the Clear button to start fresh

## 🔧 Configuration

### Ollama Connection

By default, the app connects to Ollama at `http://localhost:11434`. If your Ollama instance is running elsewhere, you'll need to modify the API endpoints in the code.

### Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview the production build
- `npm run clean` - Clean build artifacts

## 📁 Project Structure

```
OG-Ollama-UI/
├── src/
│   ├── components/ui/    # shadcn/ui components
│   ├── hooks/           # Custom React hooks
│   ├── lib/             # Utility functions
│   ├── pages/           # Page components
│   ├── App.tsx          # Main app component
│   └── main.tsx         # Entry point
├── scripts/
│   └── build.mjs        # Build configuration
├── rebeldev-backend/    # Backend API (in development)
├── tools/               # Development tools
├── dist/                # Build output
└── public files...
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Guidelines

1. **Code Style**: The project uses Prettier for code formatting
2. **TypeScript**: Maintain type safety throughout the codebase
3. **Components**: Follow shadcn/ui patterns for new components
4. **Commits**: Use clear, descriptive commit messages

## 🐛 Troubleshooting

### Common Issues

**Cannot connect to Ollama**

- Ensure Ollama is running: `ollama serve`
- Check that Ollama is accessible at `http://localhost:11434`
- Verify you have models installed: `ollama list`

**Build failures**

- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear dist folder: `npm run clean`

**CORS issues**

- Ollama should allow CORS by default for localhost
- If issues persist, check Ollama's configuration

## 🗺️ Roadmap

- [ ] **Backend API** - Complete FastAPI implementation
- [ ] **Multiple AI Providers** - OpenAI, Anthropic, Perplexity support
- [ ] **Chat History** - Persistent conversation storage
- [ ] **Custom System Prompts** - User-defined AI behavior
- [ ] **File Uploads** - Document analysis capabilities
- [ ] **Themes** - Dark/light mode toggle
- [ ] **Export Conversations** - Save chats as files

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) - For the amazing local AI platform
- [shadcn/ui](https://ui.shadcn.com/) - For the beautiful component library
- [Tailwind CSS](https://tailwindcss.com/) - For the utility-first CSS framework

---

**Made with ❤️ for the local AI community**
