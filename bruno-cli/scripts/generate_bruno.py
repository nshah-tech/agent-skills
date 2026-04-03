#!/usr/bin/env python3
"""
Bruno Collection Generator — Express & NestJS
Scans your project routes and creates/updates .bru files inside the bruno/ submodule.

Usage:
  python generate_bruno.py                              # auto-detect, runs from project root
  python generate_bruno.py --project-path /path/to/app
  python generate_bruno.py --framework nestjs
  python generate_bruno.py --framework express
  python generate_bruno.py --framework both
  python generate_bruno.py --bruno-path ./bruno         # custom bruno folder (default: ./bruno)
  python generate_bruno.py --base-url http://localhost:3000
  python generate_bruno.py --envs local,staging,production
  python generate_bruno.py --collection-name "My API"
  python generate_bruno.py --dry-run                   # preview changes, don't write files
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Route:
    method: str                        # GET POST PUT PATCH DELETE
    path: str                          # /api/users/:id
    name: str                          # "Get User by ID"
    auth: str = "none"                 # none | bearer | basic | apikey
    has_body: bool = False
    path_params: list = field(default_factory=list)   # ["id", "userId"]
    query_params: list = field(default_factory=list)  # ["page", "limit"]
    body_fields: list = field(default_factory=list)   # ["name", "email"]
    tags: list = field(default_factory=list)
    folder: str = ""                   # Bruno collection subfolder
    seq: int = 1
    source_file: str = ""
    framework: str = ""


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def to_kebab(s: str) -> str:
    """Convert a string to kebab-case for filenames."""
    s = re.sub(r'[^a-zA-Z0-9\s_-]', '', s)
    s = re.sub(r'[\s_]+', '-', s.strip())
    return s.lower()

def path_to_name(method: str, path: str) -> str:
    """Convert GET /users/:id -> 'Get User by Id'."""
    parts = [p for p in path.strip('/').split('/') if p and not p.startswith('{')]
    # Replace :param and {param} with "by Param"
    named_parts = []
    param_parts = []
    for part in path.strip('/').split('/'):
        if part.startswith(':') or (part.startswith('{') and part.endswith('}')):
            param = part.strip(':{} ').replace('-', ' ').replace('_', ' ').title()
            param_parts.append(f"by {param}")
        elif part:
            named_parts.append(part.replace('-', ' ').replace('_', ' ').title())
    label = ' '.join(named_parts + param_parts)
    return f"{method.title()} {label}".strip() if label else f"{method.title()} Root"

def path_params_from_path(path: str) -> list:
    """Extract :id and {id} style params from a path string."""
    params = re.findall(r':([a-zA-Z_][a-zA-Z0-9_]*)', path)
    params += re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', path)
    return list(dict.fromkeys(params))

def normalize_path(path: str) -> str:
    """Normalize /api//users/ -> /api/users and convert {id} -> :id."""
    path = re.sub(r'\{([^}]+)\}', r':\1', path)   # {id} -> :id
    path = re.sub(r'/+', '/', '/' + path.strip('/'))
    return path or '/'

def folder_from_path(path: str) -> str:
    """Derive a Bruno collection folder name from the route path."""
    parts = [p for p in path.strip('/').split('/') if p and not p.startswith(':')]
    if not parts:
        return 'root'
    # Skip 'api' or 'v1', 'v2' prefixes if there's more after
    skip = {'api', 'v1', 'v2', 'v3'}
    filtered = [p for p in parts if p.lower() not in skip]
    folder = filtered[0] if filtered else parts[0]
    return to_kebab(folder)

def auth_from_hints(text: str) -> str:
    """Guess auth type from guard/middleware names in source code."""
    bearer_hints = [
        'JwtAuthGuard', 'AuthGuard', 'BearerGuard', 'JwtGuard',
        'authenticate', 'verifyToken', 'requireAuth', 'isAuthenticated',
        'passport.authenticate', 'jwtMiddleware', 'authMiddleware',
        'TokenGuard', 'AccessTokenGuard', 'jwt', 'bearer'
    ]
    basic_hints = ['BasicAuthGuard', 'BasicGuard', 'basic-auth', 'basicAuth']
    apikey_hints = ['ApiKeyGuard', 'apiKey', 'api-key', 'x-api-key']

    text_lower = text.lower()
    if any(h.lower() in text_lower for h in basic_hints):
        return 'basic'
    if any(h.lower() in text_lower for h in apikey_hints):
        return 'apikey'
    if any(h.lower() in text_lower for h in bearer_hints):
        return 'bearer'
    return 'none'


# ---------------------------------------------------------------------------
# NestJS Scanner
# ---------------------------------------------------------------------------

def scan_nestjs(project_path: Path) -> list[Route]:
    """Scan NestJS project for all controller routes."""
    routes = []

    # Find all TypeScript files that likely contain controllers
    ts_files = list(project_path.rglob('*.ts'))
    controller_files = [
        f for f in ts_files
        if 'node_modules' not in str(f)
        and 'dist' not in str(f)
        and '.spec.' not in f.name
        and '.test.' not in f.name
        and (
            f.name.endswith('.controller.ts')
            or _file_has_controller_decorator(f)
        )
    ]

    for cf in controller_files:
        try:
            file_routes = _parse_nestjs_controller(cf, project_path)
            routes.extend(file_routes)
        except Exception as e:
            print(f"  ⚠  Could not parse {cf.relative_to(project_path)}: {e}")

    return routes


def _file_has_controller_decorator(path: Path) -> bool:
    try:
        content = path.read_text(encoding='utf-8', errors='ignore')
        return '@Controller(' in content or '@Controller()' in content
    except Exception:
        return False


def _parse_nestjs_controller(file_path: Path, project_root: Path) -> list[Route]:
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    routes = []

    # Extract controller prefix
    ctrl_match = re.search(
        r"@Controller\(\s*['\"]([^'\"]*)['\"]|@Controller\(\s*\{[^}]*path\s*:\s*['\"]([^'\"]*)['\"]",
        content
    )
    ctrl_prefix = ''
    if ctrl_match:
        ctrl_prefix = ctrl_match.group(1) or ctrl_match.group(2) or ''

    # Class-level auth guard
    class_auth = 'none'
    class_block = re.search(r'@Controller.*?(?=export class)', content, re.DOTALL)
    if class_block:
        class_auth = auth_from_hints(class_block.group(0))

    # Split file into method chunks by finding all HTTP method decorators
    method_pattern = re.compile(
        r'(@(?:Get|Post|Put|Patch|Delete|Head|Options|All)\s*\([^)]*\).*?)(?=@(?:Get|Post|Put|Patch|Delete|Head|Options|All|UseGuards|ApiOperation|Roles|Public|HttpCode|UseInterceptors|Injectable|Controller|Module)|export\s+class|\Z)',
        re.DOTALL
    )

    seq = 1
    for chunk_match in method_pattern.finditer(content):
        chunk = chunk_match.group(0)

        # Extract HTTP method and sub-path
        http_match = re.search(
            r'@(Get|Post|Put|Patch|Delete|Head|Options|All)\s*\(\s*(?:[\'"]([^\'"]*)[\'"]\s*)?\)',
            chunk, re.IGNORECASE
        )
        if not http_match:
            continue

        http_method = http_match.group(1).upper()
        sub_path = http_match.group(2) or ''

        full_path = normalize_path(f"{ctrl_prefix}/{sub_path}")
        path_params = path_params_from_path(full_path)

        # Auth: method-level overrides class-level
        method_auth = auth_from_hints(chunk)
        auth = method_auth if method_auth != 'none' else class_auth

        # Check for @Public() decorator → no auth
        if '@Public()' in chunk:
            auth = 'none'

        # Detect body / query / params
        has_body = '@Body()' in chunk or '@Body(' in chunk
        has_query = '@Query()' in chunk or '@Query(' in chunk
        has_param = '@Param()' in chunk or '@Param(' in chunk

        # Extract named @Query params
        query_params = re.findall(r"@Query\(['\"]([^'\"]+)['\"]\)", chunk)

        # Extract method name for a friendlier route name
        method_name_match = re.search(r'(?:async\s+)?(\w+)\s*\(', chunk.split('@')[-1])
        method_fn_name = method_name_match.group(1) if method_name_match else ''
        route_name = _fn_name_to_label(method_fn_name) if method_fn_name else path_to_name(http_method, full_path)

        folder = folder_from_path(full_path)

        route = Route(
            method=http_method,
            path=full_path,
            name=route_name,
            auth=auth,
            has_body=has_body or (http_method in ('POST', 'PUT', 'PATCH')),
            path_params=path_params,
            query_params=query_params,
            folder=folder,
            seq=seq,
            source_file=str(file_path.relative_to(project_root)),
            framework='nestjs'
        )
        routes.append(route)
        seq += 1

    return routes


def _fn_name_to_label(name: str) -> str:
    """camelCase or snake_case to 'Title Case Label'."""
    # Insert space before uppercase letters
    s = re.sub(r'([A-Z])', r' \1', name).strip()
    # Replace underscores
    s = s.replace('_', ' ')
    return s.title()


# ---------------------------------------------------------------------------
# Express Scanner
# ---------------------------------------------------------------------------

def scan_express(project_path: Path) -> list[Route]:
    """Scan Express project for all route definitions."""
    routes = []

    js_ts_files = list(project_path.rglob('*.ts')) + list(project_path.rglob('*.js'))
    router_files = [
        f for f in js_ts_files
        if 'node_modules' not in str(f)
        and 'dist' not in str(f)
        and '.spec.' not in f.name
        and '.test.' not in f.name
        and _file_has_express_routes(f)
    ]

    # Build a map of router variable name -> mount path from the app entry file
    mount_map = _build_router_mount_map(project_path)

    for rf in router_files:
        try:
            file_routes = _parse_express_router(rf, project_path, mount_map)
            routes.extend(file_routes)
        except Exception as e:
            print(f"  ⚠  Could not parse {rf.relative_to(project_path)}: {e}")

    return routes


def _file_has_express_routes(path: Path) -> bool:
    try:
        content = path.read_text(encoding='utf-8', errors='ignore')
        return bool(re.search(
            r'(?:router|app|Router)\s*\.\s*(?:get|post|put|patch|delete|use)\s*\(',
            content, re.IGNORECASE
        ))
    except Exception:
        return False


def _build_router_mount_map(project_path: Path) -> dict:
    """Try to find app.use('/path', routerName) statements to resolve prefixes."""
    mount_map = {}
    # Look in common entry file names
    entry_names = ['app.ts', 'app.js', 'main.ts', 'main.js', 'server.ts', 'server.js',
                   'index.ts', 'index.js', 'routes.ts', 'routes.js', 'routes/index.ts',
                   'routes/index.js', 'src/app.ts', 'src/app.js', 'src/main.ts', 'src/main.js']

    for name in entry_names:
        entry = project_path / name
        if entry.exists():
            try:
                content = entry.read_text(encoding='utf-8', errors='ignore')
                # Match: app.use('/prefix', routerVar)
                for m in re.finditer(
                    r'app\.use\s*\(\s*[\'"]([^\'"/][^\'"]*)[\'"]\s*,\s*(\w+)',
                    content
                ):
                    prefix, router_var = m.group(1), m.group(2)
                    mount_map[router_var] = normalize_path(prefix)
            except Exception:
                pass

    return mount_map


def _parse_express_router(file_path: Path, project_root: Path, mount_map: dict) -> list[Route]:
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    routes = []
    seq = 1

    # Detect the router variable name (e.g., `const router = express.Router()`)
    router_var_match = re.search(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:express\.Router|Router)\s*\(', content)
    router_var = router_var_match.group(1) if router_var_match else 'router'

    # Find mounted prefix from mount_map
    file_prefix = mount_map.get(router_var, '')
    if not file_prefix:
        # Try to guess from filename (e.g., users.routes.ts -> /users)
        stem = file_path.stem.replace('.routes', '').replace('.router', '').replace('Routes', '').replace('Router', '')
        if stem not in ('app', 'main', 'server', 'index', 'routes'):
            file_prefix = '/' + to_kebab(stem)

    # Match route definitions: router.METHOD('path', [middleware,] handler)
    route_pattern = re.compile(
        r'(?:' + re.escape(router_var) + r'|app|router)\s*\.\s*(get|post|put|patch|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]([^;]*?)(?=\n\s*(?:\w|\}|//)|\Z)',
        re.IGNORECASE | re.DOTALL
    )

    for m in route_pattern.finditer(content):
        http_method = m.group(1).upper()
        sub_path = m.group(2)
        handler_chunk = m.group(3)

        full_path = normalize_path(f"{file_prefix}/{sub_path}")
        path_params = path_params_from_path(full_path)

        auth = auth_from_hints(handler_chunk)

        has_body = http_method in ('POST', 'PUT', 'PATCH')

        route_name = path_to_name(http_method, full_path)
        folder = folder_from_path(full_path)

        route = Route(
            method=http_method,
            path=full_path,
            name=route_name,
            auth=auth,
            has_body=has_body,
            path_params=path_params,
            folder=folder,
            seq=seq,
            source_file=str(file_path.relative_to(project_root)),
            framework='express'
        )
        routes.append(route)
        seq += 1

    return routes


# ---------------------------------------------------------------------------
# .bru file generator
# ---------------------------------------------------------------------------

def generate_bru_content(route: Route, base_url_var: str = 'baseUrl') -> str:
    """Generate the full content of a .bru file for a route."""
    lines = []

    # meta
    lines.append('meta {')
    lines.append(f'  name: {route.name}')
    lines.append('  type: http')
    lines.append(f'  seq: {route.seq}')
    lines.append('}')
    lines.append('')

    # HTTP method block
    bru_path = route.path
    for p in route.path_params:
        bru_path = bru_path.replace(f':{p}', f'{{{{{p}}}}}')
    lines.append(f'{route.method.lower()} {{')
    lines.append(f'  url: {{{{{base_url_var}}}}}{bru_path}')
    lines.append(f'  auth: {route.auth}')
    lines.append('}')
    lines.append('')

    # Path params
    if route.path_params:
        lines.append('params:path {')
        for p in route.path_params:
            lines.append(f'  {p}: {{{{{p}}}}}')
        lines.append('}')
        lines.append('')

    # Query params (if any detected, or placeholder for GET)
    if route.query_params:
        lines.append('params:query {')
        for q in route.query_params:
            lines.append(f'  {q}: ')
        lines.append('}')
        lines.append('')
    elif route.method == 'GET' and not route.path_params:
        lines.append('params:query {')
        lines.append('  ~page: 1')
        lines.append('  ~limit: 20')
        lines.append('}')
        lines.append('')

    # Headers
    lines.append('headers {')
    if route.has_body:
        lines.append('  Content-Type: application/json')
    lines.append('  Accept: application/json')
    lines.append('}')
    lines.append('')

    # Auth block
    if route.auth == 'bearer':
        lines.append('auth:bearer {')
        lines.append('  token: {{authToken}}')
        lines.append('}')
        lines.append('')
    elif route.auth == 'basic':
        lines.append('auth:basic {')
        lines.append('  username: {{username}}')
        lines.append('  password: {{password}}')
        lines.append('}')
        lines.append('')
    elif route.auth == 'apikey':
        lines.append('auth:apikey {')
        lines.append('  key: X-API-Key')
        lines.append('  value: {{apiKey}}')
        lines.append('  placement: header')
        lines.append('}')
        lines.append('')

    # Body
    if route.has_body:
        lines.append('body:json {')
        lines.append('  {')
        if route.body_fields:
            for bf in route.body_fields:
                lines.append(f'    "{bf}": ""')
        else:
            lines.append('    ')
        lines.append('  }')
        lines.append('}')
        lines.append('')

    # Default assertions
    expected_status = '201' if route.method == 'POST' else '200'
    lines.append('assert {')
    lines.append(f'  res.status: eq {expected_status}')
    lines.append('}')
    lines.append('')

    # Placeholder tests block
    lines.append('tests {')
    lines.append(f'  test("{route.name} returns expected status", function () {{')
    lines.append(f'    expect(res.getStatus()).to.equal({expected_status});')
    lines.append('  });')
    lines.append('}')
    lines.append('')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Merge logic — preserve user-written blocks
# ---------------------------------------------------------------------------

# Blocks that come from code (we can update them)
CODE_OWNED_BLOCKS = {'meta', 'get', 'post', 'put', 'patch', 'delete', 'head',
                     'params:path', 'auth:bearer', 'auth:basic', 'auth:apikey', 'headers'}

# Blocks that belong to the user (never overwrite)
USER_OWNED_BLOCKS = {'script:pre-request', 'script:post-response', 'tests', 'assert',
                     'vars:pre-request', 'vars:post-response', 'body:json',
                     'body:form-urlencoded', 'body:multipartForm', 'params:query'}


def extract_blocks(content: str) -> dict:
    """Parse a .bru file into a dict of block_name -> full block text."""
    blocks = {}
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        # Match block opening: "blockname {" (at start of line)
        m = re.match(r'^([\w:]+)\s*\{', line.strip())
        if m and line.strip() == m.group(0):
            block_name = m.group(1)
            block_lines = [line]
            depth = line.count('{') - line.count('}')
            i += 1
            while i < len(lines) and depth > 0:
                block_lines.append(lines[i])
                depth += lines[i].count('{') - lines[i].count('}')
                i += 1
            blocks[block_name] = '\n'.join(block_lines)
        else:
            i += 1
    return blocks


def merge_bru_file(existing_content: str, new_content: str) -> str:
    """
    Merge a newly generated .bru file with existing content.
    - Code-owned blocks are taken from new_content
    - User-owned blocks are preserved from existing_content
    """
    existing_blocks = extract_blocks(existing_content)
    new_blocks = extract_blocks(new_content)

    merged_blocks = {}

    # Start with all new (code-owned) blocks
    for name, content in new_blocks.items():
        merged_blocks[name] = content

    # Overlay preserved user blocks from existing
    for name, content in existing_blocks.items():
        if name in USER_OWNED_BLOCKS and name in existing_blocks:
            # Only preserve if user has added real content beyond the placeholder
            if _has_user_content(name, content):
                merged_blocks[name] = content

    # Preserve ordering: meta, method, params:path, params:query, headers, auth, body, vars, assert, scripts, tests
    order = ['meta', 'get', 'post', 'put', 'patch', 'delete', 'head',
             'params:path', 'params:query', 'headers',
             'auth:bearer', 'auth:basic', 'auth:apikey', 'auth:oauth2',
             'body:json', 'body:form-urlencoded', 'body:multipartForm', 'body:text', 'body:xml', 'body:graphql',
             'vars:pre-request', 'vars:post-response',
             'assert', 'script:pre-request', 'script:post-response', 'tests']

    result_parts = []
    for key in order:
        if key in merged_blocks:
            result_parts.append(merged_blocks[key])

    # Any blocks not in our known order
    for key, val in merged_blocks.items():
        if key not in order:
            result_parts.append(val)

    return '\n\n'.join(result_parts) + '\n'


def _has_user_content(block_name: str, content: str) -> bool:
    """Check if a user-owned block has real user content vs empty/placeholder."""
    # Extract inner content
    inner = re.sub(r'^[\w:]+\s*\{', '', content, count=1)
    inner = re.sub(r'\}\s*$', '', inner).strip()

    if block_name == 'tests':
        return 'expect(' in inner and 'Expected status' not in inner
    if block_name == 'assert':
        return bool(inner) and not re.match(r'^\s*res\.status:\s*eq\s*\d+\s*$', inner)
    if block_name in ('script:pre-request', 'script:post-response'):
        return bool(inner) and 'console.log' not in inner
    if block_name in ('body:json', 'body:form-urlencoded'):
        return bool(inner.strip()) and inner.strip() != '{'

    return bool(inner)


# ---------------------------------------------------------------------------
# File & collection structure generators
# ---------------------------------------------------------------------------

def ensure_bruno_structure(bruno_path: Path, collection_name: str, envs: list[str], base_url: str):
    """Create bruno.json and environment files if they don't exist."""
    bruno_path.mkdir(parents=True, exist_ok=True)

    # bruno.json
    config_file = bruno_path / 'bruno.json'
    if not config_file.exists():
        config = {
            "version": "1",
            "name": collection_name,
            "type": "collection",
            "ignore": ["node_modules", ".git"]
        }
        config_file.write_text(json.dumps(config, indent=2))
        print(f"  ✓  Created {config_file.relative_to(bruno_path.parent)}")

    # environments/
    env_dir = bruno_path / 'environments'
    env_dir.mkdir(exist_ok=True)

    env_urls = {
        'local': base_url or 'http://localhost:3000',
        'staging': 'https://api.staging.example.com',
        'production': 'https://api.example.com',
    }

    for env in envs:
        env_file = env_dir / f'{env}.bru'
        if not env_file.exists():
            url = env_urls.get(env, f'https://{env}.example.com')
            env_content = f"""vars {{
  baseUrl: {url}
}}

vars:secret {{
  authToken:
  apiKey:
  username:
  password:
}}
"""
            env_file.write_text(env_content)
            print(f"  ✓  Created {env_file.relative_to(bruno_path.parent)}")


def write_bru_file(bru_path: Path, route: Route, dry_run: bool = False) -> str:
    """Write or update a .bru file. Returns 'created', 'updated', or 'unchanged'."""
    new_content = generate_bru_content(route)

    if bru_path.exists():
        existing_content = bru_path.read_text(encoding='utf-8')
        merged = merge_bru_file(existing_content, new_content)
        if merged.strip() == existing_content.strip():
            return 'unchanged'
        if not dry_run:
            bru_path.write_text(merged)
        return 'updated'
    else:
        if not dry_run:
            bru_path.parent.mkdir(parents=True, exist_ok=True)
            bru_path.write_text(new_content)
        return 'created'


def generate_collection(routes: list[Route], bruno_path: Path, dry_run: bool = False):
    """Generate all .bru files from a list of routes."""

    # Group by folder and assign sequential numbers
    from collections import defaultdict
    folder_groups = defaultdict(list)
    for r in routes:
        folder_groups[r.folder].append(r)

    stats = {'created': 0, 'updated': 0, 'unchanged': 0}

    for folder, folder_routes in sorted(folder_groups.items()):
        folder_path = bruno_path / folder
        if not dry_run:
            folder_path.mkdir(parents=True, exist_ok=True)

        # Sort by method order for sensible seq numbering
        method_order = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
        folder_routes.sort(key=lambda r: (method_order.index(r.method) if r.method in method_order else 99, r.path))

        for seq, route in enumerate(folder_routes, start=1):
            route.seq = seq
            filename = to_kebab(route.name) + '.bru'
            bru_file = folder_path / filename

            status = write_bru_file(bru_file, route, dry_run=dry_run)
            stats[status] += 1

            icon = {'created': '✓', 'updated': '↻', 'unchanged': '·'}[status]
            rel = bru_file.relative_to(bruno_path.parent) if not dry_run else f"bruno/{folder}/{filename}"
            print(f"  {icon}  [{status:9s}]  {rel}  ({route.method} {route.path})")

    return stats


# ---------------------------------------------------------------------------
# Framework detection
# ---------------------------------------------------------------------------

def detect_framework(project_path: Path) -> str:
    """Auto-detect whether a project is NestJS, Express, or both."""
    pkg_file = project_path / 'package.json'
    is_nestjs = False
    is_express = False

    if pkg_file.exists():
        try:
            pkg = json.loads(pkg_file.read_text())
            deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
            if '@nestjs/core' in deps or '@nestjs/common' in deps:
                is_nestjs = True
            if 'express' in deps:
                is_express = True
        except Exception:
            pass

    if is_nestjs and is_express:
        return 'both'
    if is_nestjs:
        return 'nestjs'
    if is_express:
        return 'express'
    return 'unknown'


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Generate Bruno collections from Express/NestJS routes')
    parser.add_argument('--project-path', default='.', help='Path to the project root (default: current directory)')
    parser.add_argument('--framework', choices=['nestjs', 'express', 'both', 'auto'], default='auto')
    parser.add_argument('--bruno-path', default='bruno', help='Path to the Bruno folder (default: ./bruno)')
    parser.add_argument('--base-url', default='http://localhost:3000', help='Base URL for the local environment')
    parser.add_argument('--envs', default='local,staging,production', help='Comma-separated environment names')
    parser.add_argument('--collection-name', default='', help='Bruno collection name (default: project folder name)')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing files')
    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()
    bruno_path = (project_path / args.bruno_path).resolve()
    envs = [e.strip() for e in args.envs.split(',')]
    collection_name = args.collection_name or project_path.name.replace('-', ' ').replace('_', ' ').title()

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Bruno Collection Generator")
    print(f"  Project : {project_path}")
    print(f"  Bruno   : {bruno_path}")
    print(f"  Envs    : {', '.join(envs)}")
    print()

    # Detect framework
    framework = args.framework
    if framework == 'auto':
        framework = detect_framework(project_path)
        print(f"  Detected framework: {framework}")
    if framework == 'unknown':
        print("  ⚠  Could not detect framework. Trying both Express and NestJS scanners.")
        framework = 'both'

    # Scan routes
    routes = []
    print("\n  Scanning routes...")
    if framework in ('nestjs', 'both'):
        nestjs_routes = scan_nestjs(project_path)
        print(f"  NestJS: found {len(nestjs_routes)} routes")
        routes.extend(nestjs_routes)
    if framework in ('express', 'both'):
        express_routes = scan_express(project_path)
        print(f"  Express: found {len(express_routes)} routes")
        routes.extend(express_routes)

    if not routes:
        print("\n  ⚠  No routes found. Check that your project path is correct.")
        sys.exit(1)

    # Deduplicate (same method + path from multiple scanners)
    seen = set()
    unique_routes = []
    for r in routes:
        key = (r.method, r.path)
        if key not in seen:
            seen.add(key)
            unique_routes.append(r)
    routes = unique_routes
    print(f"\n  Total unique routes: {len(routes)}")

    # Set up Bruno structure
    print("\n  Setting up Bruno collection structure...")
    if not args.dry_run:
        ensure_bruno_structure(bruno_path, collection_name, envs, args.base_url)

    # Generate .bru files
    print("\n  Generating .bru files...")
    stats = generate_collection(routes, bruno_path, dry_run=args.dry_run)

    print(f"\n  Done! {stats['created']} created, {stats['updated']} updated, {stats['unchanged']} unchanged.")
    if not args.dry_run:
        print(f"\n  Run your collection:\n    cd {bruno_path} && bru run --env local\n")


if __name__ == '__main__':
    main()
