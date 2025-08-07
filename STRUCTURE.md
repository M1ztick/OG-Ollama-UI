# Project Structure

## OG-Ollama-UI

A modern React-based UI for Ollama with FastAPI backend support.

```
OG-Ollama-UI/
├── 📁 src/                     # Frontend React application
│   ├── 📄 App.tsx              # Main app component with routing
│   ├── 📄 main.tsx             # React entry point
│   ├── 📄 shadcn.css           # Global styles
│   ├── 📁 components/          # React components
│   │   └── 📁 ui/              # shadcn/ui components
│   ├── 📁 hooks/               # Custom React hooks
│   ├── 📁 lib/                 # Utility functions
│   └── 📁 pages/               # Page components
│       └── 📄 Home.tsx         # Main chat interface
│
├── 📁 rebeldev-backend/        # FastAPI backend
│   ├── 📄 requirements.txt     # Python dependencies
│   ├── 📄 run.py               # Development server runner
│   ├── 📄 .env.example         # Environment configuration template
│   ├── 📁 app/                 # Main application package
│   │   ├── 📄 main.py          # FastAPI application
│   │   ├── 📄 config.py        # Configuration settings
│   │   ├── 📁 models/          # Pydantic models
│   │   │   └── 📄 schemas.py   # Request/response schemas
│   │   ├── 📁 routers/         # API route handlers
│   │   │   └── 📄 chat.py      # Chat endpoints
│   │   └── 📁 services/        # Business logic services
│   │       ├── 📄 ollama.py    # Ollama integration
│   │       ├── 📄 openai.py    # OpenAI integration
│   │       └── 📄 perplex.py   # Perplexity integration
│   ├── 📁 docs/                # API documentation
│   │   └── 📄 api.md           # API reference
│   ├── 📁 migrations/          # Database migrations (future)
│   └── 📁 tests/               # Test files
│       └── 📄 test_chat.py     # Chat API tests
│
├── 📁 scripts/                 # Build and utility scripts
│   └── 📄 build.mjs            # esbuild configuration
│
├── 📁 tools/                   # Development tools and extensions
│   ├── 📄 esbenp.prettier-vscode-11.0.0.vsix
│   └── 📄 silasnevstad.gpthelper-1.1.0.vsix
│
├── 📁 dist/                    # Build output (generated)
├── 📁 node_modules/            # Node.js dependencies (generated)
│
├── 📄 package.json             # Node.js project configuration
├── 📄 package-lock.json        # Locked dependency versions
├── 📄 tsconfig.json            # TypeScript configuration
├── 📄 tailwind.config.js       # Tailwind CSS configuration
├── 📄 index.html               # HTML entry point
├── 📄 README.md                # Project documentation
└── 📄 .gitignore               # Git ignore patterns
```

## Key Components

### Frontend (`src/`)

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **shadcn/ui** for UI components
- **React Router** for navigation
- **esbuild** for fast bundling

### Backend (`rebeldev-backend/`)

- **FastAPI** for API framework
- **Pydantic** for data validation
- **Multi-provider support** (Ollama, OpenAI, Perplexity)
- **Streaming responses** with Server-Sent Events
- **Async/await** throughout

### Build System (`scripts/`)

- **esbuild** for ultra-fast bundling
- **PostCSS** with Tailwind processing
- **Development server** with hot reload
- **Production optimizations**

## Development Workflow

1. **Frontend Development**

   ```bash
   npm run dev        # Start development server
   npm run build      # Build for production
   ```

2. **Backend Development**

   ```bash
   cd rebeldev-backend
   pip install -r requirements.txt
   python run.py      # Start FastAPI server
   ```

3. **Full Stack Development**
   - Frontend: http://localhost:8000 (esbuild dev server)
   - Backend: http://localhost:8000 (FastAPI)
   - API Docs: http://localhost:8000/docs

## Configuration

### Frontend

- Build configuration in `scripts/build.mjs`
- Tailwind config in `tailwind.config.js`
- TypeScript config in `tsconfig.json`

### Backend

- Environment variables in `.env` (copy from `.env.example`)
- Server settings in `app/config.py`
- API documentation auto-generated from Pydantic models

## Future Enhancements

- [ ] Database integration with SQLAlchemy
- [ ] User authentication and session management
- [ ] Chat history persistence
- [ ] File upload and document analysis
- [ ] Plugin system for custom AI providers
- [ ] Docker containerization
- [ ] CI/CD pipeline with GitHub Actions
