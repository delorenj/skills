# [Product Name] Product Requirements Document

**Version:** 1.0  
**Last Updated:** [Date]  
**Author:** Jarad DeLorenzo  
**Status:** Draft | In Review | Approved

---

## Executive Summary

[2-3 paragraphs providing a high-level overview of the product, its purpose, and expected impact]

**Key Points:**
- What problem does this solve?
- Who is it for?
- What makes it unique?

---

## Problem Statement

### Current Situation
[Describe the current state and pain points]

### User Impact
[Explain how users are affected by the current situation]

### Business Impact
[Describe the business implications of not solving this problem]

---

## Product Vision

### Mission
[One-sentence mission statement]

### Goals
1. **Primary Goal:** [Main objective]
2. **Secondary Goals:**
   - [Supporting objective 1]
   - [Supporting objective 2]
   - [Supporting objective 3]

### Success Metrics
| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| [KPI 1] | [Target value] | [How to measure] |
| [KPI 2] | [Target value] | [How to measure] |
| [KPI 3] | [Target value] | [How to measure] |

---

## User Personas

### Primary Persona: [Name]
- **Demographics:** [Age, location, background]
- **Goals:** [What they want to achieve]
- **Pain Points:** [Current frustrations]
- **Tech Savviness:** [Low | Medium | High]
- **Quote:** "[Typical statement from this persona]"

### Secondary Persona: [Name]
- **Demographics:** [Age, location, background]
- **Goals:** [What they want to achieve]
- **Pain Points:** [Current frustrations]
- **Tech Savviness:** [Low | Medium | High]
- **Quote:** "[Typical statement from this persona]"

---

## Core Features

### Feature 1: [Feature Name]
**Complexity:** Small | Medium | Large | XL

**Description:**
[Detailed description of the feature]

**User Value:**
[What benefit does this provide to users?]

**Implementation Notes:**
- [Technical consideration 1]
- [Technical consideration 2]

**Dependencies:**
- [Other features or systems this depends on]

**Acceptance Criteria:**
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

### Feature 2: [Feature Name]
**Complexity:** Small | Medium | Large | XL

[Same structure as Feature 1]

---

## Technical Architecture

### Tech Stack

**Frontend:**
- Framework: React + Vite + TypeScript
- Styling: Tailwind CSS
- Components: ShadCN/UI
- State: Zustand / React Query

**Backend:**
- API: FastAPI (Python 3.11+)
- Database: PostgreSQL
- Cache: Redis
- Package Manager: UV

**Infrastructure:**
- Deployment: Docker Compose
- CI/CD: GitHub Actions
- Tool Versioning: Mise
- Monitoring: [TBD]
- Logging: [TBD]

**AI/ML (if applicable):**
- Agents: Agno
- MCP: FastMCP for tool servers
- LLM: OpenAI GPT-4 / Claude
- Vector DB: Qdrant (if needed)

### System Architecture

```
┌─────────────────┐
│   Next.js Web   │
│     Frontend    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │
│   Backend       │
└────────┬────────┘
         │
    ┌────┴─────┬──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ Supabase│ │ Qdrant │ │External│
│   DB    │ │ Vector │ │  APIs  │
└────────┘ └────────┘ └────────┘
```

### Data Models

**[Entity 1]:**
```typescript
interface Entity1 {
  id: string
  name: string
  created_at: timestamp
  updated_at: timestamp
  // ... other fields
}
```

**[Entity 2]:**
```typescript
interface Entity2 {
  id: string
  entity1_id: string
  // ... other fields
}
```

### API Design

**Endpoints:**
- `GET /api/v1/[resource]` - List all
- `GET /api/v1/[resource]/:id` - Get single
- `POST /api/v1/[resource]` - Create new
- `PATCH /api/v1/[resource]/:id` - Update
- `DELETE /api/v1/[resource]/:id` - Delete

**Authentication:**
- Bearer token via Supabase Auth
- JWT validation on all protected endpoints

---

## Development Roadmap

### Phase 1: Foundation
**Complexity:** Medium  
**Dependencies:** None

**Deliverables:**
- [ ] Project setup (iMi workflow)
- [ ] Database schema
- [ ] Auth system
- [ ] Base UI components
- [ ] Docker environment

### Phase 2: Core Features
**Complexity:** Large  
**Dependencies:** Phase 1

**Deliverables:**
- [ ] Feature 1 implementation
- [ ] Feature 2 implementation
- [ ] Feature 3 implementation
- [ ] Basic testing suite

### Phase 3: Enhancement
**Complexity:** Medium  
**Dependencies:** Phase 2

**Deliverables:**
- [ ] Advanced features
- [ ] Performance optimization
- [ ] Analytics integration
- [ ] Comprehensive testing

### Phase 4: Polish & Launch
**Complexity:** Small  
**Dependencies:** Phase 3

**Deliverables:**
- [ ] UI/UX refinement
- [ ] Documentation
- [ ] Deployment automation
- [ ] Monitoring setup

---

## Complexity Assessment

### Effort Estimation Guide

**Small Complexity:**
- Simple UI component
- Basic API endpoint
- Single database table
- Estimated: 1-3 days

**Medium Complexity:**
- Feature with multiple components
- Multiple API endpoints
- Several related database tables
- Integration with external service
- Estimated: 1-2 weeks

**Large Complexity:**
- Major system feature
- Complex business logic
- Multiple service integrations
- Real-time functionality
- Estimated: 2-4 weeks

**XL Complexity:**
- Platform-level feature
- Multiple interconnected systems
- Advanced AI integration
- Mobile app development
- Estimated: 1-2 months

### Risk Assessment

| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|---------|-------------------|
| [Risk 1] | High/Med/Low | High/Med/Low | [How to mitigate] |
| [Risk 2] | High/Med/Low | High/Med/Low | [How to mitigate] |

---

## Project Organization (iMi Workflow)

### Repository Structure
```
project-name/
├── trunk-main/              # Main branch
├── feature-mvp/             # MVP features
├── feature-auth/            # Authentication
├── feature-[name]/          # Additional features
└── experiment-[idea]/       # Experiments
```

### Component Repositories

**Main Web App:**
```bash
mkdir -p ~/code/project-name
cd ~/code/project-name
gh repo clone org/project-name-web trunk-main
```

**Additional Components:**
- `project-name-api` - Backend service
- `project-name-mobile` - Mobile application
- `project-name-docs` - Documentation

---

## Non-Functional Requirements

### Performance
- API response time: < 200ms (p95)
- Page load time: < 2s (FCP)
- Database queries: < 100ms (average)

### Security
- HTTPS only
- JWT token authentication
- Rate limiting on API endpoints
- SQL injection prevention
- XSS protection

### Scalability
- Support for [X] concurrent users
- Horizontal scaling capability
- Database connection pooling
- Caching strategy

### Reliability
- 99.9% uptime target
- Automated backups
- Error monitoring and alerting
- Graceful degradation

---

## Open Questions

1. **[Question 1]**
   - Status: Open | Under Review | Resolved
   - Owner: [Name]
   - Impact: High | Medium | Low

2. **[Question 2]**
   - Status: Open | Under Review | Resolved
   - Owner: [Name]
   - Impact: High | Medium | Low

---

## Appendix

### Related Documents
- [[Technical Architecture Detailed]]
- [[API Specification]]
- [[Database Schema]]
- [[Deployment Guide]]

### References
- [External resource 1]
- [External resource 2]
- [Design inspiration]

### Changelog
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | [Date] | [Name] | Initial version |
| 1.1 | [Date] | [Name] | [Changes] |

---

**Notes:**
- This PRD uses complexity/effort metrics instead of time estimates
- All dates are relative and should be adjusted based on team velocity
- Integrate with Obsidian vault at `/Projects/[ProjectName]/PRD.md`
- Follow iMi workflow for all development work
