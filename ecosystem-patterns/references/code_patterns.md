# Code Patterns & Style Guide

## Core Architectural Principles

### Layered Abstraction
**Philosophy:** Clear separation of concerns across data, business logic, and presentation layers.

**Structure:**
```
Application
├── Data Layer          # Database models, schemas, migrations
├── Business Logic      # Services, domain logic, orchestration
└── Presentation       # API routes, UI components, views
```

**Benefits:**
- Modularity and testability
- Independent scaling
- Clear dependencies
- Easier maintenance

### API-First Design
**Philosophy:** Design APIs before implementation, treating them as contracts.

**Process:**
1. Define API specification (OpenAPI/Swagger)
2. Review and approve endpoints
3. Generate types from spec
4. Implement backend
5. Implement frontend

## Language-Specific Patterns

### Python (FastAPI)

#### Project Structure
```python
app/
├── api/
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── users.py
│   │   │   ├── projects.py
│   │   │   └── tasks.py
│   │   └── router.py
│   └── deps.py            # Dependencies
├── models/                # Database models
│   ├── __init__.py
│   ├── user.py
│   └── project.py
├── schemas/               # Pydantic schemas
│   ├── __init__.py
│   ├── user.py
│   └── project.py
├── services/              # Business logic
│   ├── __init__.py
│   ├── user_service.py
│   └── project_service.py
├── core/                  # Configuration
│   ├── __init__.py
│   ├── config.py
│   └── security.py
├── db/                    # Database
│   ├── __init__.py
│   ├── base.py
│   └── session.py
├── main.py                # Application entry
├── pyproject.toml         # UV project config
└── uv.lock                # UV lockfile
```

#### UV Package Management

**Always use UV for Python projects:**
```bash
# Initialize new project
uv init my-project
cd my-project

# Add dependencies
uv add fastapi uvicorn sqlalchemy pydantic redis

# Add dev dependencies
uv add --dev pytest pytest-asyncio black ruff

# Install dependencies
uv sync

# Run scripts
uv run python main.py
uv run pytest

# Update dependencies
uv lock --upgrade
```

**pyproject.toml pattern:**
```toml
[project]
name = "my-project"
version = "0.1.0"
description = "Project description"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.6.0",
    "redis>=5.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "black>=24.0.0",
    "ruff>=0.2.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.black]
line-length = 100
target-version = ["py311"]
```

#### Naming Conventions
```python
# Files: snake_case
user_service.py
project_manager.py

# Classes: PascalCase
class UserService:
    pass

class ProjectManager:
    pass

# Functions/methods: snake_case
def get_user_by_id(user_id: int):
    pass

async def create_project(project_data: ProjectCreate):
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
API_VERSION = "v1"

# Private methods: _leading_underscore
def _validate_user_data(data: dict):
    pass
```

#### Type Hints (Always)
```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# Function signatures
def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[User]:
    pass

# Async functions
async def fetch_data(
    url: str,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    pass

# Pydantic models
class UserCreate(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    
    class Config:
        orm_mode = True
```

#### FastAPI Patterns
```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse

app = FastAPI(title="API Name", version="1.0.0")

# Dependency injection
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current authenticated user."""
    user = verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user

# Router pattern
router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users with pagination."""
    users = await user_service.get_users(db, skip=skip, limit=limit)
    return users

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user."""
    try:
        user = await user_service.create_user(db, user_data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Include router in main app
app.include_router(router)
```

#### Error Handling
```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Custom exceptions
class UserNotFoundError(Exception):
    pass

class InsufficientPermissionsError(Exception):
    pass

# Exception handlers
@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": "User not found"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
```

### TypeScript (React + Vite)

#### Project Structure
```typescript
src/
├── main.tsx               # Application entry point
├── App.tsx                # Root component
├── components/            # React components
│   ├── ui/               # ShadCN components
│   ├── features/         # Feature-specific
│   └── shared/           # Shared components
├── lib/                   # Utilities
│   ├── api.ts            # API client
│   ├── utils.ts          # Helper functions
│   └── db.ts             # Database client (if applicable)
├── types/                 # TypeScript types
│   ├── database.ts       # Database types
│   └── api.ts            # API types
├── hooks/                 # Custom hooks
│   ├── useAuth.ts
│   └── useProjects.ts
├── store/                 # State management (Zustand)
│   ├── auth.ts
│   └── projects.ts
├── routes/                # Route definitions
│   └── index.tsx
└── styles/                # Global styles
    └── globals.css
```

#### Naming Conventions
```typescript
// Files: kebab-case for components, camelCase for utilities
user-card.tsx
project-list.tsx
apiClient.ts
dateUtils.ts

// Components: PascalCase
export function UserCard({ user }: UserCardProps) {
  return <div>{user.name}</div>
}

export default function ProjectList() {
  return <div>Projects</div>
}

// Functions: camelCase
function formatDate(date: Date): string {
  return date.toISOString()
}

async function fetchProjects(): Promise<Project[]> {
  return await api.get('/projects')
}

// Constants: UPPER_SNAKE_CASE
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL
const MAX_UPLOAD_SIZE = 5 * 1024 * 1024

// Types/Interfaces: PascalCase
interface UserCardProps {
  user: User
  onEdit?: (user: User) => void
}

type ProjectStatus = 'active' | 'completed' | 'archived'
```

#### Type Definitions
```typescript
// Always define explicit types
interface User {
  id: string
  email: string
  name: string | null
  created_at: string
  updated_at: string
}

// Use type for unions and intersections
type ApiResponse<T> = {
  data: T
  error: null
} | {
  data: null
  error: string
}

// Generic types
interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
}

// Utility types
type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>
type Required<T, K extends keyof T> = T & { [P in K]-?: T[P] }
```

#### React Patterns

**Component Structure:**
```typescript
// For client-side rendering (Vite default)
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import type { User } from '@/types/database'

interface UserProfileProps {
  userId: string
  onUpdate?: (user: User) => void
}

export function UserProfile({ userId, onUpdate }: UserProfileProps) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function loadUser() {
      try {
        const data = await fetchUser(userId)
        setUser(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load user')
      } finally {
        setLoading(false)
      }
    }

    loadUser()
  }, [userId])

  if (loading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={error} />
  if (!user) return null

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">{user.name}</h2>
      <p className="text-muted-foreground">{user.email}</p>
      <Button onClick={() => onUpdate?.(user)}>
        Edit Profile
      </Button>
    </div>
  )
}
```

**Zustand State Management:**
```typescript
// stores/auth.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      
      login: async (email, password) => {
        const { user, token } = await api.login(email, password)
        set({ user, token, isAuthenticated: true })
      },
      
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false })
      },
      
      setUser: (user) => {
        set({ user })
      }
    }),
    {
      name: 'auth-storage', // localStorage key
      partialize: (state) => ({
        token: state.token,
        user: state.user
      })
    }
  )
)

// Usage in components
function Dashboard() {
  const { user, logout } = useAuthStore()
  
  return (
    <div>
      <h1>Welcome, {user?.name}</h1>
      <button onClick={logout}>Logout</button>
    </div>
  )
}
```

**React Router Setup:**
```typescript
// routes/index.tsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { ProtectedRoute } from '@/components/ProtectedRoute'

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Home />
      },
      {
        path: 'dashboard',
        element: (
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        )
      },
      {
        path: 'projects',
        children: [
          {
            index: true,
            element: <ProjectList />
          },
          {
            path: ':id',
            element: <ProjectDetail />
          }
        ]
      }
    ]
  },
  {
    path: '/login',
    element: <Login />
  }
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
```
```

**Custom Hooks:**
```typescript
import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'

export function useProjects() {
  const { user } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!user) return

    const fetchProjects = async () => {
      try {
        setLoading(true)
        const data = await api.getProjects()
        setProjects(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch'))
      } finally {
        setLoading(false)
      }
    }

    fetchProjects()
  }, [user])

  const createProject = async (data: ProjectCreate) => {
    const newProject = await api.createProject(data)
    setProjects(prev => [...prev, newProject])
    return newProject
  }

  return { projects, loading, error, createProject }
}
```

**API Client Pattern:**
```typescript
// lib/api.ts
import axios, { AxiosInstance } from 'axios'
import { useAuthStore } from '@/stores/auth'

class ApiClient {
  private client: AxiosInstance

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Add auth interceptor
    this.client.interceptors.request.use((config) => {
      const token = useAuthStore.getState().token
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Add error interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          useAuthStore.getState().logout()
        }
        return Promise.reject(error)
      }
    )
  }

  // Generic methods
  async get<T>(url: string, params?: object): Promise<T> {
    const response = await this.client.get<T>(url, { params })
    return response.data
  }

  async post<T>(url: string, data: object): Promise<T> {
    const response = await this.client.post<T>(url, data)
    return response.data
  }

  async put<T>(url: string, data: object): Promise<T> {
    const response = await this.client.put<T>(url, data)
    return response.data
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url)
    return response.data
  }

  // Resource-specific methods
  async getProjects(): Promise<Project[]> {
    return this.get<Project[]>('/api/v1/projects')
  }

  async createProject(data: ProjectCreate): Promise<Project> {
    return this.post<Project>('/api/v1/projects', data)
  }

  async updateProject(id: string, data: Partial<Project>): Promise<Project> {
    return this.put<Project>(`/api/v1/projects/${id}`, data)
  }

  async deleteProject(id: string): Promise<void> {
    return this.delete(`/api/v1/projects/${id}`)
  }
}

export const api = new ApiClient(import.meta.env.VITE_API_URL)
```

**Vite Environment Variables:**
```typescript
// vite-env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_NAME: string
  // Add more env variables as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// .env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=My App
```
```

### FastMCP (Model Context Protocol)

**Philosophy:** FastMCP provides high-level abstractions for building MCP servers quickly and correctly.

#### Basic MCP Server Pattern
```python
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("My Tool Server")

# Define a tool
@mcp.tool()
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    return a + b

# Define a resource
@mcp.resource("config://settings")
def get_settings() -> dict:
    """Get application settings."""
    return {
        "version": "1.0.0",
        "features": ["calculation", "data_processing"]
    }

# Define a prompt
@mcp.prompt()
def code_review_prompt(code: str) -> str:
    """Generate a code review prompt."""
    return f"Review this code for best practices:\n\n{code}"

# Run the server
if __name__ == "__main__":
    mcp.run()
```

#### Advanced Tool Patterns
```python
from fastmcp import FastMCP, Context
from typing import Annotated

mcp = FastMCP("Advanced Tools")

# Tool with context
@mcp.tool()
async def search_documents(
    query: str,
    ctx: Annotated[Context, "MCP context"]
) -> list[dict]:
    """Search documents with progress tracking."""
    await ctx.info(f"Searching for: {query}")
    
    results = await perform_search(query)
    
    await ctx.info(f"Found {len(results)} results")
    return results

# Tool with validation
@mcp.tool()
def process_file(
    file_path: Annotated[str, "Path to file"],
    format: Annotated[str, "Output format (json|xml|csv)"] = "json"
) -> dict:
    """Process a file and return data in specified format."""
    if format not in ["json", "xml", "csv"]:
        raise ValueError(f"Unsupported format: {format}")
    
    return {"status": "processed", "format": format}

# Tool with progress updates
@mcp.tool()
async def batch_process(
    items: list[str],
    ctx: Context
) -> dict:
    """Process multiple items with progress tracking."""
    total = len(items)
    processed = 0
    
    for item in items:
        await process_item(item)
        processed += 1
        await ctx.info(f"Progress: {processed}/{total}")
    
    return {"total": total, "processed": processed}
```

#### Resource Patterns
```python
# Static resource
@mcp.resource("config://database")
def get_db_config() -> dict:
    return {
        "host": "localhost",
        "port": 5432,
        "database": "myapp"
    }

# Dynamic resource with URI template
@mcp.resource("user://{user_id}/profile")
async def get_user_profile(user_id: str) -> dict:
    """Get user profile by ID."""
    user = await fetch_user(user_id)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email
    }

# Resource with metadata
@mcp.resource(
    "data://analytics",
    name="Analytics Data",
    description="Current analytics metrics",
    mime_type="application/json"
)
async def get_analytics() -> dict:
    """Get real-time analytics data."""
    return await fetch_analytics()
```

#### Project Structure
```
my-mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py          # Main MCP server
│   ├── tools/             # Tool implementations
│   │   ├── __init__.py
│   │   ├── files.py
│   │   └── search.py
│   ├── resources/         # Resource providers
│   │   ├── __init__.py
│   │   └── config.py
│   └── prompts/           # Prompt templates
│       ├── __init__.py
│       └── templates.py
├── tests/
│   └── test_server.py
├── pyproject.toml
└── README.md
```

### Agno Agents

**Philosophy:** Agno provides a framework for building autonomous AI agents with structured workflows and tool integration.

#### Basic Agent Pattern
```python
from agno import Agent, task

class ResearchAgent(Agent):
    """Agent for conducting research tasks."""
    
    def __init__(self):
        super().__init__(
            name="Researcher",
            role="Research and information gathering",
            model="gpt-4"
        )
    
    @task
    async def research_topic(self, topic: str) -> dict:
        """Research a topic and provide summary."""
        # Agent automatically uses available tools
        search_results = await self.search_web(topic)
        summary = await self.analyze_results(search_results)
        
        return {
            "topic": topic,
            "summary": summary,
            "sources": search_results
        }
    
    @task
    async def fact_check(self, claim: str) -> dict:
        """Verify a claim against multiple sources."""
        sources = await self.find_sources(claim)
        verification = await self.cross_reference(claim, sources)
        
        return {
            "claim": claim,
            "verified": verification["is_verified"],
            "confidence": verification["confidence"],
            "sources": sources
        }
```

#### Multi-Agent Coordination
```python
from agno import Agent, Swarm

# Define specialized agents
code_reviewer = Agent(
    name="CodeReviewer",
    role="Review code for quality and security",
    model="gpt-4"
)

documentation_writer = Agent(
    name="DocWriter",
    role="Write technical documentation",
    model="gpt-4"
)

# Create agent swarm
dev_team = Swarm([code_reviewer, documentation_writer])

# Coordinate agents on task
async def process_pull_request(pr_url: str):
    """Process a PR with multiple agents."""
    # Code review agent analyzes code
    review = await code_reviewer.review_pr(pr_url)
    
    # Documentation agent updates docs
    docs = await documentation_writer.update_docs(
        changes=review["changes"],
        pr_url=pr_url
    )
    
    return {
        "review": review,
        "documentation": docs
    }
```

#### Agent with Tools
```python
from agno import Agent, tool

class DataAnalyst(Agent):
    """Agent for data analysis tasks."""
    
    def __init__(self):
        super().__init__(
            name="Analyst",
            role="Data analysis and visualization",
            tools=[self.load_data, self.analyze_stats, self.create_viz]
        )
    
    @tool
    async def load_data(self, source: str) -> pd.DataFrame:
        """Load data from source."""
        return pd.read_csv(source)
    
    @tool
    async def analyze_stats(self, df: pd.DataFrame) -> dict:
        """Compute statistical analysis."""
        return {
            "mean": df.mean().to_dict(),
            "std": df.std().to_dict(),
            "correlations": df.corr().to_dict()
        }
    
    @tool
    async def create_viz(self, df: pd.DataFrame, chart_type: str) -> str:
        """Create visualization and return path."""
        fig = create_chart(df, chart_type)
        path = f"outputs/{chart_type}.png"
        fig.savefig(path)
        return path
```

#### Agent Workflow Pattern
```python
from agno import Agent, Workflow, Step

# Define workflow steps
class DataPipeline(Workflow):
    """Multi-step data processing workflow."""
    
    @Step(order=1)
    async def extract(self, source: str) -> dict:
        """Extract data from source."""
        data = await self.agent.load_data(source)
        return {"data": data, "status": "extracted"}
    
    @Step(order=2)
    async def transform(self, data: dict) -> dict:
        """Transform and clean data."""
        cleaned = await self.agent.clean_data(data["data"])
        return {"data": cleaned, "status": "transformed"}
    
    @Step(order=3)
    async def analyze(self, data: dict) -> dict:
        """Analyze transformed data."""
        analysis = await self.agent.analyze(data["data"])
        return {"analysis": analysis, "status": "complete"}

# Run workflow
analyst = DataAnalyst()
pipeline = DataPipeline(agent=analyst)
result = await pipeline.run(source="data.csv")
```

### SQL (PostgreSQL)

#### Naming Conventions
```sql
-- Tables: lowercase with underscores, plural
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Columns: lowercase with underscores
user_id
first_name
created_at
is_active

-- Indexes: table_column_idx
CREATE INDEX user_profiles_email_idx ON user_profiles(email);
CREATE INDEX projects_user_id_idx ON projects(user_id);

-- Foreign keys: table_column_fkey
ALTER TABLE projects
ADD CONSTRAINT projects_user_id_fkey
FOREIGN KEY (user_id) REFERENCES user_profiles(id);

-- Functions: lowercase with underscores
CREATE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

#### Standard Patterns
```sql
-- Timestamps on all tables
created_at TIMESTAMPTZ DEFAULT NOW()
updated_at TIMESTAMPTZ DEFAULT NOW()

-- Soft deletes
deleted_at TIMESTAMPTZ

-- Auto-update trigger
CREATE TRIGGER update_user_profiles_updated_at
BEFORE UPDATE ON user_profiles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS)
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
ON user_profiles FOR SELECT
USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
ON user_profiles FOR UPDATE
USING (auth.uid() = id);
```

## Comment Patterns

### Python Comments
```python
# Single-line comment for simple explanations

def complex_function(param: str) -> dict:
    """
    Multi-line docstring for functions.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param is invalid
    """
    # Implementation note
    result = process_param(param)
    
    # TODO: Add caching here
    return result

# NOTE: Important architectural decision
# FIXME: Known issue that needs addressing
# HACK: Temporary workaround
```

### TypeScript Comments
```typescript
// Single-line comment

/**
 * Multi-line JSDoc comment for functions/components.
 * 
 * @param userId - The user's unique identifier
 * @param options - Configuration options
 * @returns Promise resolving to user data
 * @throws {Error} If user not found
 */
async function fetchUser(
  userId: string,
  options?: FetchOptions
): Promise<User> {
  // Implementation
}

// TODO: Implement caching
// FIXME: Handle edge case
// NOTE: Performance consideration
```

## Testing Patterns

### Python (pytest)
```python
# tests/test_user_service.py
import pytest
from app.services.user_service import UserService

@pytest.fixture
def user_service(db_session):
    return UserService(db_session)

def test_create_user_success(user_service):
    """Test successful user creation."""
    # Arrange
    user_data = {"email": "test@example.com", "name": "Test User"}
    
    # Act
    user = user_service.create_user(user_data)
    
    # Assert
    assert user.email == "test@example.com"
    assert user.name == "Test User"

@pytest.mark.asyncio
async def test_fetch_user_not_found(user_service):
    """Test handling of non-existent user."""
    with pytest.raises(UserNotFoundError):
        await user_service.get_user_by_id("nonexistent")
```

### TypeScript (Jest/Vitest)
```typescript
// __tests__/userService.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { UserService } from '@/services/userService'

describe('UserService', () => {
  let userService: UserService

  beforeEach(() => {
    userService = new UserService()
  })

  it('should create user successfully', async () => {
    // Arrange
    const userData = { email: 'test@example.com', name: 'Test User' }
    
    // Act
    const user = await userService.createUser(userData)
    
    // Assert
    expect(user.email).toBe('test@example.com')
    expect(user.name).toBe('Test User')
  })

  it('should throw error for duplicate email', async () => {
    // Arrange
    const userData = { email: 'duplicate@example.com', name: 'Test' }
    await userService.createUser(userData)
    
    // Act & Assert
    await expect(userService.createUser(userData))
      .rejects.toThrow('Email already exists')
  })
})
```

## Git Commit Patterns

### Conventional Commits
```bash
# Format: <type>(<scope>): <description>

feat(auth): add JWT token validation
fix(api): resolve race condition in user creation
docs(readme): update installation instructions
style(ui): improve button hover states
refactor(db): optimize query performance
test(user): add integration tests
chore(deps): update dependencies

# Breaking changes
feat(api)!: change authentication flow

BREAKING CHANGE: Auth endpoints now require OAuth
```

### Commit Messages
```
Short summary (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain the problem being solved and why this approach was chosen.

- Bullet points for multiple changes
- Use present tense ("Add feature" not "Added feature")
- Reference issues: "Fixes #123" or "Related to #456"
```

## Best Practices

### Code Organization
1. **File length:** Keep files under 300 lines
2. **Function length:** Keep functions under 50 lines
3. **Class methods:** Keep under 20 lines
4. **Complexity:** Avoid nesting beyond 3 levels

### Performance
1. **Database:** Index foreign keys and frequently queried columns
2. **API:** Implement pagination for list endpoints
3. **Frontend:** Lazy load components and images
4. **Caching:** Cache expensive computations and API calls

### Security
1. **Input validation:** Validate all user input
2. **SQL injection:** Use parameterized queries
3. **XSS:** Sanitize user-generated content
4. **Secrets:** Never commit secrets to version control
5. **Auth:** Implement proper JWT validation

### Documentation
1. **README:** Clear setup and usage instructions
2. **API docs:** OpenAPI/Swagger specification
3. **Code comments:** Explain "why" not "what"
4. **Inline docs:** Use docstrings/JSDoc
5. **Architecture:** Document major decisions
