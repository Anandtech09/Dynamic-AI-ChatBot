# Python Programming — Quick Reference

## What is Python?

Python is a high-level, interpreted, general-purpose programming language. Created by Guido van Rossum and first released in 1991, Python emphasises code readability with its clean syntax and significant indentation.

## Key Features

- **Easy to Learn**: Clear, readable syntax
- **Versatile**: Web development, data science, AI/ML, automation, and more
- **Large Ecosystem**: Thousands of packages on PyPI
- **Cross-Platform**: Runs on Windows, macOS, Linux
- **Dynamic Typing**: Variables don't need type declarations
- **Interpreted**: No compilation step needed

## Common Frameworks

### Web Development
- **FastAPI**: Modern, fast web framework for building APIs with Python 3.7+ type hints
- **Django**: Full-featured web framework with ORM, admin, and templating
- **Flask**: Lightweight micro-framework for web applications

### Data Science
- **NumPy**: Numerical computing with arrays
- **Pandas**: Data manipulation and analysis
- **Matplotlib**: Data visualisation

### Machine Learning
- **scikit-learn**: Traditional ML algorithms
- **TensorFlow**: Deep learning framework by Google
- **PyTorch**: Deep learning framework by Meta

## Python Decorators

Decorators are a way to modify or enhance functions without changing their source code. They use the `@` syntax:

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before function call")
        result = func(*args, **kwargs)
        print("After function call")
        return result
    return wrapper

@my_decorator
def greet(name):
    print(f"Hello, {name}!")
```

Common use cases:
- Logging
- Authentication
- Caching
- Rate limiting
- Input validation

## Virtual Environments

Virtual environments isolate project dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

## FastAPI

FastAPI is a modern Python web framework known for:
- **Speed**: One of the fastest Python frameworks
- **Type Safety**: Built on Pydantic for data validation
- **Auto Documentation**: Automatic OpenAPI (Swagger) docs
- **Async Support**: Full async/await support
- **Dependency Injection**: Built-in DI system

Example:
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello/{name}")
async def hello(name: str):
    return {"message": f"Hello, {name}!"}
```
