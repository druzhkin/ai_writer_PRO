#!/usr/bin/env python3
"""
API documentation generation script using OpenAPI specification with comprehensive endpoint documentation.
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
import requests
from datetime import datetime


class APIDocumentationGenerator:
    """Generate comprehensive API documentation from OpenAPI specification."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.openapi_url = f"{base_url}/openapi.json"
        self.docs_dir = Path("docs")
        self.api_docs_dir = self.docs_dir / "api"
        
    def create_directories(self):
        """Create documentation directories."""
        self.docs_dir.mkdir(exist_ok=True)
        self.api_docs_dir.mkdir(exist_ok=True)
        
    def fetch_openapi_spec(self) -> Dict[str, Any]:
        """Fetch OpenAPI specification from the API."""
        try:
            response = requests.get(self.openapi_url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching OpenAPI spec: {e}")
            sys.exit(1)
    
    def generate_endpoint_documentation(self, spec: Dict[str, Any]) -> str:
        """Generate comprehensive endpoint documentation."""
        docs = []
        
        # Add header
        docs.append("# API Endpoints Documentation")
        docs.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        docs.append(f"API Version: {spec.get('info', {}).get('version', 'Unknown')}")
        docs.append(f"Base URL: {spec.get('servers', [{}])[0].get('url', self.base_url)}")
        docs.append("")
        
        # Add authentication section
        if 'components' in spec and 'securitySchemes' in spec['components']:
            docs.append("## Authentication")
            docs.append("")
            for scheme_name, scheme in spec['components']['securitySchemes'].items():
                docs.append(f"### {scheme_name}")
                docs.append(f"- **Type**: {scheme.get('type', 'Unknown')}")
                if 'description' in scheme:
                    docs.append(f"- **Description**: {scheme['description']}")
                docs.append("")
        
        # Group endpoints by tags
        endpoints_by_tag = {}
        for path, methods in spec.get('paths', {}).items():
            for method, details in methods.items():
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    tags = details.get('tags', ['Untagged'])
                    for tag in tags:
                        if tag not in endpoints_by_tag:
                            endpoints_by_tag[tag] = []
                        endpoints_by_tag[tag].append({
                            'path': path,
                            'method': method.upper(),
                            'details': details
                        })
        
        # Generate documentation for each tag
        for tag, endpoints in endpoints_by_tag.items():
            docs.append(f"## {tag}")
            docs.append("")
            
            for endpoint in endpoints:
                path = endpoint['path']
                method = endpoint['method']
                details = endpoint['details']
                
                # Endpoint header
                docs.append(f"### {method} {path}")
                docs.append("")
                
                # Description
                if 'summary' in details:
                    docs.append(f"**Summary**: {details['summary']}")
                    docs.append("")
                
                if 'description' in details:
                    docs.append(f"**Description**: {details['description']}")
                    docs.append("")
                
                # Parameters
                if 'parameters' in details:
                    docs.append("**Parameters**:")
                    docs.append("")
                    for param in details['parameters']:
                        docs.append(f"- `{param['name']}` ({param.get('in', 'unknown')})")
                        docs.append(f"  - **Type**: {param.get('schema', {}).get('type', 'unknown')}")
                        docs.append(f"  - **Required**: {param.get('required', False)}")
                        if 'description' in param:
                            docs.append(f"  - **Description**: {param['description']}")
                        docs.append("")
                
                # Request body
                if 'requestBody' in details:
                    docs.append("**Request Body**:")
                    docs.append("")
                    content = details['requestBody'].get('content', {})
                    for content_type, content_details in content.items():
                        docs.append(f"- **Content Type**: {content_type}")
                        if 'schema' in content_details:
                            schema = content_details['schema']
                            if '$ref' in schema:
                                docs.append(f"  - **Schema**: {schema['$ref']}")
                            else:
                                docs.append(f"  - **Schema**: {json.dumps(schema, indent=2)}")
                        docs.append("")
                
                # Responses
                if 'responses' in details:
                    docs.append("**Responses**:")
                    docs.append("")
                    for status_code, response_details in details['responses'].items():
                        docs.append(f"- **{status_code}**: {response_details.get('description', 'No description')}")
                        if 'content' in response_details:
                            content = response_details['content']
                            for content_type, content_details in content.items():
                                docs.append(f"  - **Content Type**: {content_type}")
                                if 'schema' in content_details:
                                    schema = content_details['schema']
                                    if '$ref' in schema:
                                        docs.append(f"    - **Schema**: {schema['$ref']}")
                                    else:
                                        docs.append(f"    - **Schema**: {json.dumps(schema, indent=2)}")
                        docs.append("")
                
                # Security
                if 'security' in details:
                    docs.append("**Security**:")
                    docs.append("")
                    for security_requirement in details['security']:
                        for scheme_name, scopes in security_requirement.items():
                            docs.append(f"- **{scheme_name}**: {', '.join(scopes) if scopes else 'No scopes'}")
                    docs.append("")
                
                docs.append("---")
                docs.append("")
        
        return "\n".join(docs)
    
    def generate_schema_documentation(self, spec: Dict[str, Any]) -> str:
        """Generate schema documentation."""
        docs = []
        
        docs.append("# API Schemas Documentation")
        docs.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        docs.append("")
        
        if 'components' in spec and 'schemas' in spec['components']:
            schemas = spec['components']['schemas']
            
            for schema_name, schema in schemas.items():
                docs.append(f"## {schema_name}")
                docs.append("")
                
                if 'description' in schema:
                    docs.append(f"**Description**: {schema['description']}")
                    docs.append("")
                
                if 'type' in schema:
                    docs.append(f"**Type**: {schema['type']}")
                    docs.append("")
                
                if 'properties' in schema:
                    docs.append("**Properties**:")
                    docs.append("")
                    for prop_name, prop_details in schema['properties'].items():
                        docs.append(f"- `{prop_name}`")
                        docs.append(f"  - **Type**: {prop_details.get('type', 'unknown')}")
                        if 'description' in prop_details:
                            docs.append(f"  - **Description**: {prop_details['description']}")
                        if 'format' in prop_details:
                            docs.append(f"  - **Format**: {prop_details['format']}")
                        if 'example' in prop_details:
                            docs.append(f"  - **Example**: {prop_details['example']}")
                        docs.append("")
                
                docs.append("---")
                docs.append("")
        
        return "\n".join(docs)
    
    def generate_examples_documentation(self, spec: Dict[str, Any]) -> str:
        """Generate API examples documentation."""
        docs = []
        
        docs.append("# API Examples Documentation")
        docs.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        docs.append("")
        
        # Authentication examples
        docs.append("## Authentication Examples")
        docs.append("")
        docs.append("### Login")
        docs.append("```bash")
        docs.append("curl -X POST \\")
        docs.append("  http://localhost:8000/api/v1/auth/login \\")
        docs.append("  -H 'Content-Type: application/json' \\")
        docs.append("  -d '{")
        docs.append('    "email": "user@example.com",')
        docs.append('    "password": "password123"')
        docs.append("  }'")
        docs.append("```")
        docs.append("")
        
        docs.append("### Register")
        docs.append("```bash")
        docs.append("curl -X POST \\")
        docs.append("  http://localhost:8000/api/v1/auth/register \\")
        docs.append("  -H 'Content-Type: application/json' \\")
        docs.append("  -d '{")
        docs.append('    "email": "user@example.com",')
        docs.append('    "password": "password123",')
        docs.append('    "username": "username",')
        docs.append('    "first_name": "John",')
        docs.append('    "last_name": "Doe"')
        docs.append("  }'")
        docs.append("```")
        docs.append("")
        
        # Content generation examples
        docs.append("## Content Generation Examples")
        docs.append("")
        docs.append("### Generate Content")
        docs.append("```bash")
        docs.append("curl -X POST \\")
        docs.append("  http://localhost:8000/api/v1/content/generate \\")
        docs.append("  -H 'Content-Type: application/json' \\")
        docs.append("  -H 'Authorization: Bearer YOUR_TOKEN' \\")
        docs.append("  -d '{")
        docs.append('    "title": "My Article",')
        docs.append('    "brief": "Article brief",')
        docs.append('    "target_words": 1000,')
        docs.append('    "style_profile_id": "style-id"')
        docs.append("  }'")
        docs.append("```")
        docs.append("")
        
        # Style management examples
        docs.append("## Style Management Examples")
        docs.append("")
        docs.append("### Create Style Profile")
        docs.append("```bash")
        docs.append("curl -X POST \\")
        docs.append("  http://localhost:8000/api/v1/styles/ \\")
        docs.append("  -H 'Content-Type: application/json' \\")
        docs.append("  -H 'Authorization: Bearer YOUR_TOKEN' \\")
        docs.append("  -d '{")
        docs.append('    "name": "Professional Style",')
        docs.append('    "description": "Professional writing style",')
        docs.append('    "tone": "professional",')
        docs.append('    "voice": "authoritative",')
        docs.append('    "target_audience": "business"')
        docs.append("  }'")
        docs.append("```")
        docs.append("")
        
        return "\n".join(docs)
    
    def generate_error_codes_documentation(self, spec: Dict[str, Any]) -> str:
        """Generate error codes documentation."""
        docs = []
        
        docs.append("# API Error Codes Documentation")
        docs.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        docs.append("")
        
        # Common HTTP status codes
        error_codes = {
            400: "Bad Request - The request was invalid or cannot be served",
            401: "Unauthorized - Authentication is required and has failed or has not been provided",
            403: "Forbidden - The request was valid but the server is refusing action",
            404: "Not Found - The requested resource could not be found",
            422: "Unprocessable Entity - The request was well-formed but contains semantic errors",
            429: "Too Many Requests - Rate limit exceeded",
            500: "Internal Server Error - A generic error message when an unexpected condition was encountered",
            502: "Bad Gateway - The server was acting as a gateway or proxy and received an invalid response",
            503: "Service Unavailable - The server is currently unavailable"
        }
        
        docs.append("## HTTP Status Codes")
        docs.append("")
        for code, description in error_codes.items():
            docs.append(f"- **{code}**: {description}")
        docs.append("")
        
        # API-specific error codes
        docs.append("## API-Specific Error Codes")
        docs.append("")
        docs.append("- **AUTH_001**: Invalid credentials")
        docs.append("- **AUTH_002**: Token expired")
        docs.append("- **AUTH_003**: Insufficient permissions")
        docs.append("- **CONTENT_001**: Content generation failed")
        docs.append("- **CONTENT_002**: Invalid style profile")
        docs.append("- **STYLE_001**: Style analysis failed")
        docs.append("- **FILE_001**: File upload failed")
        docs.append("- **FILE_002**: Invalid file type")
        docs.append("- **RATE_001**: Rate limit exceeded")
        docs.append("")
        
        return "\n".join(docs)
    
    def generate_rate_limiting_documentation(self) -> str:
        """Generate rate limiting documentation."""
        docs = []
        
        docs.append("# Rate Limiting Documentation")
        docs.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        docs.append("")
        
        docs.append("## Rate Limits")
        docs.append("")
        docs.append("The API implements rate limiting to ensure fair usage and system stability.")
        docs.append("")
        
        docs.append("### Default Limits")
        docs.append("")
        docs.append("- **General API calls**: 60 requests per minute")
        docs.append("- **Content generation**: 10 requests per minute")
        docs.append("- **File uploads**: 20 requests per minute")
        docs.append("- **Authentication**: 5 requests per minute")
        docs.append("")
        
        docs.append("### Rate Limit Headers")
        docs.append("")
        docs.append("The API includes the following headers in responses:")
        docs.append("")
        docs.append("- `X-RateLimit-Limit`: The rate limit ceiling for the given request")
        docs.append("- `X-RateLimit-Remaining`: The number of requests left for the current window")
        docs.append("- `X-RateLimit-Reset`: The time at which the current rate limit window resets")
        docs.append("")
        
        docs.append("### Handling Rate Limits")
        docs.append("")
        docs.append("When the rate limit is exceeded, the API returns a `429 Too Many Requests` status code.")
        docs.append("The client should wait for the specified time before making another request.")
        docs.append("")
        
        return "\n".join(docs)
    
    def generate_changelog_documentation(self) -> str:
        """Generate changelog documentation."""
        docs = []
        
        docs.append("# API Changelog")
        docs.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        docs.append("")
        
        docs.append("## Version 0.1.0 (Current)")
        docs.append("")
        docs.append("### Added")
        docs.append("- Initial API release")
        docs.append("- User authentication and registration")
        docs.append("- Content generation with AI")
        docs.append("- Style profile management")
        docs.append("- File upload and processing")
        docs.append("- Organization management")
        docs.append("- Usage tracking and analytics")
        docs.append("- OAuth integration (Google, GitHub)")
        docs.append("- Comprehensive error handling")
        docs.append("- Rate limiting")
        docs.append("- API documentation")
        docs.append("")
        
        docs.append("### Changed")
        docs.append("- N/A (Initial release)")
        docs.append("")
        
        docs.append("### Deprecated")
        docs.append("- N/A (Initial release)")
        docs.append("")
        
        docs.append("### Removed")
        docs.append("- N/A (Initial release)")
        docs.append("")
        
        docs.append("### Fixed")
        docs.append("- N/A (Initial release)")
        docs.append("")
        
        return "\n".join(docs)
    
    def generate_index_documentation(self) -> str:
        """Generate index documentation."""
        docs = []
        
        docs.append("# AI Writer PRO API Documentation")
        docs.append(f"\nGenerated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        docs.append("")
        
        docs.append("## Overview")
        docs.append("")
        docs.append("The AI Writer PRO API provides comprehensive endpoints for AI-powered content generation, style analysis, and content management.")
        docs.append("")
        
        docs.append("## Quick Start")
        docs.append("")
        docs.append("1. **Authentication**: Obtain an API token by logging in or registering")
        docs.append("2. **Make Requests**: Include the token in the Authorization header")
        docs.append("3. **Handle Responses**: Check status codes and response formats")
        docs.append("")
        
        docs.append("## Documentation Sections")
        docs.append("")
        docs.append("- [API Endpoints](api/endpoints.md) - Complete endpoint documentation")
        docs.append("- [API Schemas](api/schemas.md) - Data models and schemas")
        docs.append("- [API Examples](api/examples.md) - Usage examples and code samples")
        docs.append("- [Error Codes](api/error-codes.md) - Error handling and status codes")
        docs.append("- [Rate Limiting](api/rate-limiting.md) - Rate limiting information")
        docs.append("- [Changelog](api/changelog.md) - API version history")
        docs.append("")
        
        docs.append("## Base URL")
        docs.append("")
        docs.append("```
http://localhost:8000/api/v1
```")
        docs.append("")
        
        docs.append("## Authentication")
        docs.append("")
        docs.append("The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:")
        docs.append("")
        docs.append("```
Authorization: Bearer YOUR_JWT_TOKEN
```")
        docs.append("")
        
        docs.append("## Response Format")
        docs.append("")
        docs.append("All API responses are in JSON format and include appropriate HTTP status codes.")
        docs.append("")
        
        return "\n".join(docs)
    
    def generate_all_documentation(self):
        """Generate all documentation files."""
        print("Generating API documentation...")
        
        # Create directories
        self.create_directories()
        
        # Fetch OpenAPI specification
        print("Fetching OpenAPI specification...")
        spec = self.fetch_openapi_spec()
        
        # Generate documentation files
        print("Generating endpoint documentation...")
        endpoint_docs = self.generate_endpoint_documentation(spec)
        with open(self.api_docs_dir / "endpoints.md", "w") as f:
            f.write(endpoint_docs)
        
        print("Generating schema documentation...")
        schema_docs = self.generate_schema_documentation(spec)
        with open(self.api_docs_dir / "schemas.md", "w") as f:
            f.write(schema_docs)
        
        print("Generating examples documentation...")
        examples_docs = self.generate_examples_documentation(spec)
        with open(self.api_docs_dir / "examples.md", "w") as f:
            f.write(examples_docs)
        
        print("Generating error codes documentation...")
        error_docs = self.generate_error_codes_documentation(spec)
        with open(self.api_docs_dir / "error-codes.md", "w") as f:
            f.write(error_docs)
        
        print("Generating rate limiting documentation...")
        rate_limit_docs = self.generate_rate_limiting_documentation()
        with open(self.api_docs_dir / "rate-limiting.md", "w") as f:
            f.write(rate_limit_docs)
        
        print("Generating changelog documentation...")
        changelog_docs = self.generate_changelog_documentation()
        with open(self.api_docs_dir / "changelog.md", "w") as f:
            f.write(changelog_docs)
        
        print("Generating index documentation...")
        index_docs = self.generate_index_documentation()
        with open(self.docs_dir / "README.md", "w") as f:
            f.write(index_docs)
        
        # Save OpenAPI specification
        print("Saving OpenAPI specification...")
        with open(self.api_docs_dir / "openapi.json", "w") as f:
            json.dump(spec, f, indent=2)
        
        with open(self.api_docs_dir / "openapi.yaml", "w") as f:
            yaml.dump(spec, f, default_flow_style=False)
        
        print("Documentation generation completed!")
        print(f"Documentation saved to: {self.docs_dir.absolute()}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate API documentation")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                       help="Base URL of the API (default: http://localhost:8000)")
    
    args = parser.parse_args()
    
    generator = APIDocumentationGenerator(args.base_url)
    generator.generate_all_documentation()


if __name__ == "__main__":
    main()
