# Project Rules

## Core Logic TDD
- All core logic implementation (excluding UI components) MUST follow Test Driven Development (TDD) practices.
    - **Exception**: UI components and interactions should NOT be automated. Manual verification is required for UI.
- Write tests before implementing the actual logic.
- Ensure all tests pass before committing code.

## UI Testing
- **DO NOT** write automated tests for UI components (e.g., Streamlit widgets, browser interactions).
- UI testing must be performed manually.

## SOLID Principles
- All code implementation MUST adhere to SOLID principles:
    - **S**ingle Responsibility Principle: A class should have one and only one reason to change.
    - **O**pen/Closed Principle: Objects or entities should be open for extension but closed for modification.
    - **L**iskov Substitution Principle: Objects of a superclass shall be replaceable with objects of its subclasses without breaking the application.
    - **I**nterface Segregation Principle: No client should be forced to depend on methods it does not use.
    - **D**ependency Inversion Principle: Depend on abstractions, not on concretions.
