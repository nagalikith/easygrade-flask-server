import json
from typing import Any, Dict

from fastapi import Request
from starlette.exceptions import NoMatchFound
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


def template_response(request: Request, template_name: str, context: Dict[str, Any]):
    context = dict(context)
    context["request"] = request
    return templates.TemplateResponse(template_name, context)


def safe_url_for(request: Request, name: str, default: str = "/", **params: Any) -> str:
    try:
        return str(request.url_for(name, **params))
    except NoMatchFound:
        return default


def redirect_to(url: str) -> RedirectResponse:
    return RedirectResponse(url)


def json_payload(data: Dict[str, Any]) -> str:
    return json.dumps(data)
