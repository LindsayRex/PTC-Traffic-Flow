# GitHub Copilot Instructions for ptc_traffic_flow project

## 1. Project Overview & Core Technologies

This project is a web application developed using:

*   **Language:** Python (specifically targeting **Python 3.12.9+**). Please generate code compatible with this version, utilizing modern features like f-strings, type hints (standard library `typing` module), and walrus operator where appropriate and readable.
*   **Web Framework:** **Streamlit**. Generate code using Streamlit's components (`st.button`, `st.text_input`, etc.), state management (`st.session_state`), caching (`@st.cache_data`, `@st.cache_resource`), and layouts (`st.columns`, `st.container`). Assume a standard Streamlit execution model.
*   **ORM:** **SQLAlchemy** (Core and ORM). Prefer the **Declarative Mapping** style for models. Use `Session` objects for database interactions, ensuring proper transaction management (commit/rollback/close). Adhere to SQLAlchemy best practices.
*   **Database:** **PostgreSQL**. While SQLAlchemy abstracts most interactions, be mindful of this backend if suggesting very specific SQL constructs or performance optimizations (though prefer standard SQLAlchemy).
*   **Testing Framework:** **Pytest**. All tests should be written using Pytest conventions.
*   **Development Methodology:** **Test-Driven Development (TDD)**. This is crucial.

## 2. Coding Style & General Principles

*   **PEP 8:** Strictly adhere to PEP 8 guidelines. Prioritize readability. Assume formatting might be handled by tools like Black or Ruff.
*   **Type Hinting:** Mandatory. Generate comprehensive type hints for all function signatures, variables, and class attributes using Python 3.9+ syntax.
*   **Docstrings:** Generate clear docstrings for modules, classes, functions, and methods (Google or reStructuredText format preferred). Explain purpose, arguments, returns, and any exceptions raised.
*   **Modularity:** Generate small, focused functions and classes adhering to the Single Responsibility Principle.
*   **Error Handling:** Use specific exception types in `try...except` blocks. Avoid bare `except:`. Log errors appropriately (assume standard `logging` module unless otherwise specified).
*   **Imports:** Use standard import conventions (e.g., `import streamlit as st`, `import sqlalchemy as sa`, `from sqlalchemy.orm import Session`, `import pytest`). Group imports according to PEP 8.

## 3. Technology-Specific Instructions

*   **Streamlit:**
    *   Use `st.session_state` for preserving state across reruns. Initialize keys reliably.
    *   Apply `@st.cache_data` or `@st.cache_resource` appropriately to optimize performance, especially for database queries or expensive computations.
    *   Structure UI logically using columns, containers, forms, etc.
*   **SQLAlchemy:**
    *   Generate model classes inheriting from a declarative base.
    *   Database operations must occur within a `Session` context (e.g., using a context manager `with Session(...) as session:`).
    *   When querying relationships, suggest efficient loading strategies (`selectinload`, `joinedload`) if complex queries are implied. Avoid N+1 problems.
    *   Do NOT generate raw SQL strings unless explicitly asked. Use the ORM or Core expression language.

## 4. Test Generation Instructions (Guiding Chat for `@workspace /tests`)

*   **TDD Workflow:**
    *   When asked to implement a feature, **first suggest Pytest test cases** that would fail for the missing implementation.
    *   When given a failing test, **generate the minimal code** needed to make it pass.
    *   When asked to refactor, ensure suggestions **maintain passing tests**.
*   **Pytest Focus:**
    *   Generate tests using **Pytest** syntax and features.
    *   Utilize **Pytest fixtures** heavily for setup and teardown (e.g., database sessions, test data, mocked objects). If fixtures seem appropriate, suggest their use or generate code assuming they exist (e.g., a `db_session` fixture).
    *   Use clear, specific `assert` statements.
    *   Employ **parametrization** (`@pytest.mark.parametrize`) for testing multiple scenarios efficiently.
    *   Use **mocking** (`unittest.mock` or the `mocker` fixture from `pytest-mock`) to isolate units, especially for database interactions or external services in unit tests. Integration tests might use a real test database connection (managed by fixtures).
    *   Tests should be **independent and deterministic**.

## 5. What to Avoid

*   **Suggesting alternative frameworks/libraries:** Do not suggest Flask, Django, FastAPI, Peewee, `unittest` (unless for mocking), etc., unless specifically requested as part of a comparison. Stick to the defined stack.
*   **Generating overly complex or obscure code:** Prioritize clarity and maintainability.
*   **Generating raw SQL:** Use SQLAlchemy ORM/Core unless explicitly required.
*   **Ignoring Type Hints or Docstrings:** These are mandatory.

By adhering to these instructions, you will help maintain consistency and quality within this project's specific technology stack and development methodology.