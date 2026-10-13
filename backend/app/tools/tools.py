"""
Tool system — lightweight callable tools the AI can invoke.

Each tool has a schema (name, description, parameters) and an execute method.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class Tool(ABC):
    """Base class for all tools."""

    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool and return a result dict."""
        ...

    def schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class CalculatorTool(Tool):
    """Performs safe arithmetic calculations."""

    name = "calculator"
    description = "Evaluate a mathematical expression. Supports basic arithmetic, powers, square roots, and common math functions."
    parameters = {
        "expression": {
            "type": "string",
            "description": "A mathematical expression to evaluate, e.g. '2 + 3 * 4' or 'sqrt(144)'"
        }
    }

    # Allowed names for safe eval
    _SAFE_NAMES = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sqrt": math.sqrt,
        "pow": pow,
        "log": math.log,
        "log10": math.log10,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "pi": math.pi,
        "e": math.e,
        "ceil": math.ceil,
        "floor": math.floor,
    }

    async def execute(self, expression: str = "", **kwargs) -> Dict[str, Any]:
        try:
            # Sanitize: allow only digits, operators, parentheses, dots, spaces, and known function names
            cleaned = expression.strip()
            if not cleaned:
                return {"error": "No expression provided"}

            result = eval(cleaned, {"__builtins__": {}}, self._SAFE_NAMES)
            return {
                "result": result,
                "expression": cleaned,
                "formatted": f"{cleaned} = {result}",
            }
        except Exception as e:
            return {"error": f"Could not evaluate: {str(e)}"}


class DateTimeTool(Tool):
    """Returns the current date and time."""

    name = "datetime"
    description = "Get the current date and time in the server's timezone."
    parameters = {
        "format": {
            "type": "string",
            "description": "Optional strftime format string. Default: '%Y-%m-%d %H:%M:%S'",
        }
    }

    async def execute(self, format: str = "%Y-%m-%d %H:%M:%S", **kwargs) -> Dict[str, Any]:
        now = datetime.now()
        return {
            "datetime": now.strftime(format),
            "timestamp": now.isoformat(),
            "day_of_week": now.strftime("%A"),
        }


class KnowledgeSearchTool(Tool):
    """Searches the local knowledge base using semantic similarity."""

    name = "knowledge_search"
    description = "Search the knowledge base for relevant documents and information."
    parameters = {
        "query": {
            "type": "string",
            "description": "The search query to find relevant documents."
        }
    }

    def __init__(self, rag_service=None):
        self._rag_service = rag_service

    async def execute(self, query: str = "", **kwargs) -> Dict[str, Any]:
        if not self._rag_service:
            return {"results": [], "message": "Knowledge base not configured"}
        try:
            results = await self._rag_service.search(query, top_k=3)
            return {
                "results": results,
                "query": query,
                "count": len(results),
            }
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}


# ── Tool Registry ────────────────────────────────────────────────────────────

class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_schemas(self) -> List[Dict[str, Any]]:
        return [t.schema() for t in self._tools.values()]

    def list_names(self) -> List[str]:
        return list(self._tools.keys())

    async def execute(self, name: str, **kwargs) -> Dict[str, Any]:
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}
        return await tool.execute(**kwargs)


def create_tool_registry(rag_service=None) -> ToolRegistry:
    """Create and populate the default tool registry."""
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(DateTimeTool())
    registry.register(KnowledgeSearchTool(rag_service))
    return registry
