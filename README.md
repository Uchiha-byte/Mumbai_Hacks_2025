# 🔍 TruthScan - AI-Powered Misinformation Detection System

![TruthScan Banner](https://img.shields.io/badge/TruthScan-AI%20Detection-blue?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Next.js](https://img.shields.io/badge/Next.js-16.0-black?style=for-the-badge&logo=next.js)

**TruthScan** is an advanced AI-powered platform designed to detect and analyze misinformation across multiple media types including text, images, audio, and video. Built with cutting-edge AI technologies, it provides fast and accurate analysis to help users verify content authenticity.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [API Endpoints](#-api-endpoints)
- [Setup Instructions](#-setup-instructions)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Workflow](#-workflow)
- [Environment Variables](#-environment-variables)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Core Capabilities
- **🔤 Text Analysis**: AI-generated text detection and fact-checking using LangChain agents and Tavily search
- **🖼️ Image Forensics**: Advanced image manipulation detection with EXIF analysis, hash verification, and forensic algorithms
- **🎵 Audio Verification**: Audio deepfake detection and authenticity verification
- **🎥 Video Analysis**: Video manipulation detection and frame-by-frame analysis
- **⚡ Quick Check**: Fast similarity-based analysis (2-5 second response time)
- **🤖 Multi-Agent System**: Supervisor agent pattern for intelligent routing to specialized agents
- **📊 Feedback System**: User feedback collection for continuous improvement
- **📈 Analytics**: System statistics and performance metrics

### User Experience
- **Modern UI**: Beautiful, responsive interface built with Next.js and Tailwind CSS
- **Smooth Animations**: Enhanced UX with Framer Motion and GSAP
- **Real-time Analysis**: Instant feedback with loading states and progress indicators
- **Detailed Reports**: Comprehensive analysis results with confidence scores and evidence

---

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.104.1+ | High-performance async web framework |
| **Python** | 3.10+ | Core programming language |
| **LangChain** | 0.1.0+ | AI agent orchestration and LLM integration |
| **Google Gemini** | 1.52.0+ | Advanced reasoning and text analysis |
| **HuggingFace** | Latest | AI model inference (text, image, video detection) |
| **Tavily** | 0.7.13+ | Web search for fact-checking |
| **Sentence Transformers** | 2.2.2+ | Text embeddings for similarity search |
| **FAISS** | 1.7.4+ | Fast similarity search and clustering |
| **Pillow** | 10.1.0+ | Image processing |
| **OpenCV** | 4.12.0+ | Computer vision and image forensics |
| **ImageHash** | 4.3.1+ | Perceptual image hashing |
| **ExifRead** | 3.0.0+ | EXIF metadata extraction |
| **Pydantic** | 2.5.0+ | Data validation and settings management |
| **Uvicorn** | 0.24.0+ | ASGI server |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.0.3 | React framework with App Router |
| **React** | 19.2.0 | UI library |
| **TypeScript** | 5+ | Type-safe JavaScript |
| **Tailwind CSS** | 4 | Utility-first CSS framework |
| **Framer Motion** | 12.23.24+ | Animation library |
| **GSAP** | 3.13.0+ | Professional-grade animation |
| **Lucide React** | 0.554.0+ | Icon library |
| **clsx** | 2.1.1+ | Conditional className utility |

### Development Tools
- **ESLint**: Code linting
- **PostCSS**: CSS processing
- **Python-dotenv**: Environment variable management
- **Git**: Version control

---

## 🏗️ Architecture

### System Overview

```mermaid
graph TB
    subgraph "Frontend - Next.js"
        UI[User Interface]
        Pages[Pages: Home, Quick Check, Analyze]
        Components[Components: Navbar, Forms, Cards]
    end
    
    subgraph "Backend - FastAPI"
        API[API Layer]
        Supervisor[Supervisor Agent]
        
        subgraph "Specialized Agents"
            TextAgent[Text Agent]
            ImageAgent[Image Agent]
            AudioAgent[Audio Agent]
            VideoAgent[Video Agent]
            QuickAgent[Quick Analyzer]
        end
        
        subgraph "Core Services"
            LLM[LLM Service - Gemini]
            Embeddings[Embeddings Manager]
            Forensics[Forensics Engine]
            HF[HuggingFace Client]
            Storage[Storage Service]
        end
    end
    
    subgraph "External APIs"
        Gemini[Google Gemini API]
        HFAPI[HuggingFace API]
        Tavily[Tavily Search API]
    end
    
    UI --> API
    API --> Supervisor
    API --> QuickAgent
    
    Supervisor --> TextAgent
    Supervisor --> ImageAgent
    Supervisor --> AudioAgent
    Supervisor --> VideoAgent
    
    TextAgent --> LLM
    TextAgent --> HF
    ImageAgent --> Forensics
    QuickAgent --> Embeddings
    QuickAgent --> Forensics
    
    LLM --> Gemini
    HF --> HFAPI
    TextAgent --> Tavily
    
    API --> Storage
```

### Agent Architecture

#### 1. **Supervisor Agent**
- **Role**: Intelligent request routing
- **Function**: Analyzes incoming requests and routes to appropriate specialist agent
- **Tools**: Text, Image, Audio, Video analysis specialists

#### 2. **Text Analysis Agent**
- **Tools**: 
  - AI Text Detector (HuggingFace)
  - Tavily Web Search (fact-checking)
- **Output**: Structured analysis with verdict, confidence, and evidence

#### 3. **Image Forensics Agent**
- **Capabilities**:
  - EXIF metadata analysis
  - Perceptual hashing (pHash, dHash, aHash)
  - Manipulation detection
  - Error Level Analysis (ELA)
- **Output**: Forensics report with manipulation score

#### 4. **Audio Verification Agent**
- **Purpose**: Detect audio deepfakes and manipulations
- **Integration**: HuggingFace audio models

#### 5. **Video Analysis Agent**
- **Purpose**: Frame-by-frame video analysis
- **Integration**: HuggingFace video models

#### 6. **Quick Analyzer**
- **Purpose**: Fast analysis using similarity search
- **Speed**: 2-5 second response time
- **Method**: 
  - Text: Embedding-based similarity to known hoaxes
  - Image: Fast forensics checks
- **Use Case**: Real-time verification needs

---

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### 1. **Root Endpoint**
```http
GET /
```
**Response:**
```json
{
  "message": "Welcome to TruthScan API",
  "status": "operational"
}
```

#### 2. **Health Check**
```http
GET /health
```
**Response:**
```json
{
  "status": "ok"
}
```

#### 3. **Standard Analysis** (Deep Analysis)
```http
POST /api/v1/analyze
```
**Request Body:**
```json
{
  "content": "Text or URL to analyze",
  "content_type": "text | image | audio | video"
}
```
**Response:**
```json
{
  "result": "Detailed analysis report",
  "agent_used": "Text Analysis Agent"
}
```
**Processing Time**: 10-30 seconds (full agent reasoning)

#### 4. **Quick Analysis** (Fast Check)
```http
POST /api/v1/quick-analyze
```
**Request Body:**
```json
{
  "content": "Text or image data",
  "content_type": "text | image",
  "metadata": {}
}
```
**Response:**
```json
{
  "verdict": "FAKE | SUSPECT | MIXED | VERIFIED",
  "confidence": 85,
  "summary_one_liner": "Brief summary of findings",
  "tl_dr_bullets": [
    "Key finding 1",
    "Key finding 2",
    "Key finding 3"
  ],
  "evidence": [
    {
      "type": "similarity_match | image_forensics",
      "score": 0.92,
      "details": {}
    }
  ],
  "reasons": [
    "Reason for verdict 1",
    "Reason for verdict 2"
  ]
}
```
**Processing Time**: 2-5 seconds (similarity search + forensics)

#### 5. **Submit Feedback**
```http
POST /api/v1/feedback
```
**Request Body:**
```json
{
  "analysis_id": "optional-uuid",
  "original_content": "Content that was analyzed",
  "predicted_verdict": "FAKE",
  "user_verdict": "VERIFIED",
  "user_confidence": 4,
  "comments": "Optional user comments"
}
```
**Response:**
```json
{
  "status": "success",
  "feedback_id": "uuid",
  "message": "Feedback recorded. Thank you for helping improve accuracy!"
}
```

#### 6. **System Statistics**
```http
GET /api/v1/stats
```
**Response:**
```json
{
  "storage": {
    "total_analyses": 1234,
    "total_feedback": 567
  },
  "embeddings": {
    "total_vectors": 5000,
    "index_size": "2.3 MB"
  }
}
```

---

## 🚀 Setup Instructions

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: 18.0 or higher
- **npm**: 9.0 or higher
- **Git**: Latest version

### 1. Clone the Repository
```bash
git clone https://github.com/Uchiha-byte/TruthScan_Proto.git
cd TruthScan-main
```

### 2. Backend Setup

#### Step 1: Navigate to Backend Directory
```bash
cd backend
```

#### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Configure Environment Variables
Create a `.env` file in the `backend` directory:

```env
# AI API Keys
GOOGLE_API_KEY=your_google_gemini_api_key
HUGGINGFACE_API_TOKEN=your_huggingface_token
TAVILY_API_KEY=your_tavily_api_key

# Database (Optional - for production)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Security
SECRET_KEY=your_secure_random_string_here
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Get Your API Keys:**
- **Google Gemini**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **HuggingFace**: [HuggingFace Settings](https://huggingface.co/settings/tokens)
- **Tavily**: [Tavily](https://tavily.com/)

#### Step 5: Run Backend Server
```bash
uvicorn app.main:app --reload
```
Backend will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### 3. Frontend Setup

#### Step 1: Navigate to Frontend Directory
```bash
cd ../frontend
```

#### Step 2: Install Dependencies
```bash
npm install
```

#### Step 3: Run Development Server
```bash
npm run dev
```
Frontend will be available at: `http://localhost:3000`

### 4. Verify Installation

1. **Backend**: Visit `http://localhost:8000/health` - should return `{"status": "ok"}`
2. **Frontend**: Visit `http://localhost:3000` - should display the TruthScan homepage
3. **API Docs**: Visit `http://localhost:8000/docs` - interactive API documentation

---

## 💡 Usage

### Quick Check (Fast Analysis)

1. Navigate to **Quick Check** page
2. Enter text or upload an image
3. Click **Analyze**
4. Get results in 2-5 seconds with:
   - Verdict (FAKE/SUSPECT/MIXED/VERIFIED)
   - Confidence score
   - Summary and evidence

### Deep Analysis (Full Agent Reasoning)

1. Navigate to **Analyze** page
2. Select content type (Text, Image, Audio, Video)
3. Provide content
4. Submit for analysis
5. Receive comprehensive report (10-30 seconds)

### API Usage Example

```python
import requests

# Quick Analysis
response = requests.post(
    "http://localhost:8000/api/v1/quick-analyze",
    json={
        "content": "Breaking: Scientists discover cure for all diseases!",
        "content_type": "text",
        "metadata": {}
    }
)

result = response.json()
print(f"Verdict: {result['verdict']}")
print(f"Confidence: {result['confidence']}%")
print(f"Summary: {result['summary_one_liner']}")
```

---

## 📁 Project Structure

```
TruthScan-main/
├── backend/
│   ├── app/
│   │   ├── agents/              # AI Agents
│   │   │   ├── supervisor.py    # Supervisor agent (routing)
│   │   │   ├── text_agent.py    # Text analysis agent
│   │   │   ├── image_agent.py   # Image forensics agent
│   │   │   ├── audio_agent.py   # Audio verification agent
│   │   │   ├── video_agent.py   # Video analysis agent
│   │   │   └── quick_agent.py   # Fast analyzer
│   │   ├── api/
│   │   │   └── endpoints.py     # API routes
│   │   ├── core/
│   │   │   ├── config.py        # Configuration
│   │   │   ├── llm.py           # LLM service (Gemini)
│   │   │   ├── embeddings.py    # Embeddings manager
│   │   │   ├── forensics.py     # Image forensics
│   │   │   ├── huggingface.py   # HuggingFace client
│   │   │   ├── storage.py       # Data storage
│   │   │   └── database.py      # Database connection
│   │   └── main.py              # FastAPI app entry
│   ├── data/                    # Data storage
│   ├── requirements.txt         # Python dependencies
│   └── .env                     # Environment variables
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # Home page
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── globals.css      # Global styles
│   │   │   ├── quick-check/
│   │   │   │   └── page.tsx     # Quick check page
│   │   │   └── analyze/
│   │   │       └── page.tsx     # Deep analysis page
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   └── Navbar.tsx   # Navigation bar
│   │   │   ├── analysis/
│   │   │   │   └── AnalysisForm.tsx
│   │   │   └── ui/              # UI components
│   │   │       ├── DotGrid.tsx
│   │   │       ├── ScrollReveal.tsx
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       └── textarea.tsx
│   │   └── lib/
│   │       └── utils.ts         # Utility functions
│   ├── public/                  # Static assets
│   ├── package.json             # Node dependencies
│   ├── tailwind.config.ts       # Tailwind configuration
│   └── tsconfig.json            # TypeScript config
├── legacy_prototype/            # Legacy code (reference)
├── API.md                       # API setup guide
└── README.md                    # This file
```

---

## 🔄 Workflow

### Text Analysis Workflow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Supervisor
    participant TextAgent
    participant LLM
    participant Tavily
    participant HF as HuggingFace

    User->>Frontend: Submit text for analysis
    Frontend->>API: POST /api/v1/analyze
    API->>Supervisor: Route request
    Supervisor->>TextAgent: Delegate to text specialist
    TextAgent->>HF: AI text detection
    HF-->>TextAgent: Detection result
    TextAgent->>Tavily: Fact-check search
    Tavily-->>TextAgent: Search results
    TextAgent->>LLM: Generate analysis
    LLM-->>TextAgent: Structured report
    TextAgent-->>API: Return analysis
    API-->>Frontend: JSON response
    Frontend-->>User: Display results
```

### Quick Analysis Workflow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant QuickAgent
    participant Embeddings
    participant Forensics

    User->>Frontend: Submit content (quick check)
    Frontend->>API: POST /api/v1/quick-analyze
    
    alt Text Content
        API->>QuickAgent: Analyze text
        QuickAgent->>Embeddings: Similarity search
        Embeddings-->>QuickAgent: Similar hoaxes
        QuickAgent->>QuickAgent: Calculate verdict
    else Image Content
        API->>QuickAgent: Analyze image
        QuickAgent->>Forensics: Run forensics
        Forensics-->>QuickAgent: Manipulation score
        QuickAgent->>QuickAgent: Calculate verdict
    end
    
    QuickAgent-->>API: Quick result (2-5s)
    API-->>Frontend: JSON response
    Frontend-->>User: Display verdict
```

---

## 🔐 Environment Variables

### Required Variables

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `GOOGLE_API_KEY` | Google Gemini API key for LLM | [Google AI Studio](https://makersuite.google.com/app/apikey) |
| `HUGGINGFACE_API_TOKEN` | HuggingFace API token | [HuggingFace Settings](https://huggingface.co/settings/tokens) |
| `TAVILY_API_KEY` | Tavily search API key | [Tavily](https://tavily.com/) |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | None (uses local storage) |
| `SECRET_KEY` | JWT secret key | Auto-generated (change in production) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | 30 |

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Google Gemini** for advanced LLM capabilities
- **HuggingFace** for AI model inference
- **Tavily** for web search integration
- **LangChain** for agent orchestration
- **Next.js** team for the amazing framework

---

## 📧 Contact

For questions, issues, or suggestions:
- **GitHub Issues**: [Create an issue](https://github.com/Uchiha-byte/TruthScan_Proto/issues)
- **Repository**: [TruthScan_Proto](https://github.com/Uchiha-byte/TruthScan_Proto)

---

## 🔮 Future Enhancements

- [ ] Real-time video stream analysis
- [ ] Multi-language support
- [ ] Browser extension
- [ ] Mobile application
- [ ] Advanced reporting and analytics dashboard
- [ ] Integration with social media platforms
- [ ] Blockchain-based verification records
- [ ] Community-driven fact-checking

---

**Built with ❤️ by the TruthScan Team**
