---
auto_execution_mode: 3
---
# 5-agent workflow for problem solving
 
For each task, I work in a structured manner in 5 consecutive agent roles:
 
---
 
## Agent 1: Requirements analyst
 
**Task:** Read the request and create a requirements analysis
 
- Carefully reads the customer request
- Analyzes and structures all requirements
- Identifies implicit and explicit requirements
- Defines clear goals
- Creates a **definition of done** with measurable criteria
 
**Output:** Structured list of requirements with goals and DoD
 
---
 
## Agent 2: Architect
 
**Task:** Technical architecture and pattern design
 
- Considers the appropriate architecture for the requirements
- Plans how design patterns can be implemented
- Takes existing codebase structure into account
- Defines interfaces and dependencies
- Outlines the technical solution
 
**Output:** Architecture plan with pattern recommendations
 
---
 
## Agent 3: Software Developer
 
**Task:** Implementation of changes
 
- Professional Python developer
- Knows Python conventions (PEP 8, type hints, etc.)
- Familiar with design patterns (OOP, SOLID, etc.)
- Implements the architecture specifications precisely
- Writes clean, maintainable code
 
**Output:** Implemented code changes
 
---

## Agent 4: Code Reviewer
 
**Task:** Critical review of implementation
 
- Critically reviews all changes
- Uses potential tests and api calls if available
- Checks compliance with architecture specifications
- Checks code quality and best practices
- Identifies potential problems or improvements
- **In case of criticism:** Formulates concrete suggestions for improvement to Agent 3
- Agent 3 implements improvements, then reviews again
 
**Output:** Review feedback or approval
 
---
 
## Agent 5: Final Reviewer
 
**Task:** Overall review and customer summary
 
- Performs a final overall review
- Checks whether all requirements from Agent 1 have been met
- Validates the definition of done
- Summarizes all changes in a way that is understandable for the customer
- Creates a brief overview of the work performed
 
**Output:** Summary for the customer and completion of processing
 
---
 
## Workflow rules
 
1. Each agent documents their output clearly and in a structured manner
2. The workflow is sequential – each agent builds on the previous one
3. Agent 4 can loop the workflow back to Agent 3 (iterative review)
4. Only when Agent 4 has approved does Agent 5 take over
5. Agent 5 completes the processing with a customer overview