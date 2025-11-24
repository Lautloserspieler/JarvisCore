import json
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import requests
from urllib.parse import urljoin

@dataclass
class ApiEndpoint:
    """Represents an API endpoint configuration"""
    name: str
    url: str
    method: str = 'GET'
    params: Dict[str, Any] = None
    headers: Dict[str, str] = None
    description: str = ""
    requires_auth: bool = False

class ApiManager:
    """Manages API configurations and requests for knowledge sources"""
    
    def __init__(self, config_file: str = None):
        """
        Initialize the API Manager with configurations from a JSON file
        
        Args:
            config_file: Path to the JSON configuration file
        """
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if no handlers are present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.apis: Dict[str, Dict] = {}
        self.config_file = config_file or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'config', 
            'knowledge_apis.json'
        )
        self._load_apis()
        
    def _load_apis(self):
        """Load API configurations from the JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.apis = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"API configuration file not found: {self.config_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in API configuration: {e}")
    
    def get_api_list(self) -> List[Dict]:
        """Get a list of all available APIs with basic information"""
        return [
            {
                'id': api_id,
                'name': api_data.get('name', api_id),
                'description': api_data.get('description', ''),
                'base_url': api_data.get('base_url', ''),
                'requires_auth': any(key in api_data for key in ['api_key', 'auth_required'])
            }
            for api_id, api_data in self.apis.items()
        ]
    
    def get_api_endpoint(self, api_id: str, endpoint_name: str = None, **kwargs) -> ApiEndpoint:
        """
        Get a configured API endpoint
        
        Args:
            api_id: The ID of the API (e.g., 'wikipedia_de')
            endpoint_name: Optional endpoint name for APIs with multiple endpoints
            **kwargs: Parameters to format into the URL and query parameters
            
        Returns:
            Configured ApiEndpoint object
        """
        if api_id not in self.apis:
            raise ValueError(f"API not found: {api_id}")
            
        api_config = self.apis[api_id]
        base_url = api_config['base_url']
        
        # Handle APIs with multiple endpoints
        if 'endpoints' in api_config and endpoint_name:
            if endpoint_name not in api_config['endpoints']:
                raise ValueError(f"Endpoint '{endpoint_name}' not found in API {api_id}")
            endpoint_path = api_config['endpoints'][endpoint_name]
            url = urljoin(base_url, endpoint_path)
            name = f"{api_config.get('name', api_id)} - {endpoint_name}"
        else:
            url = base_url
            name = api_config.get('name', api_id)
        
        # Format URL with provided parameters
        url = url.format(**kwargs)
        
        # Prepare parameters
        params = api_config.get('params', {}).copy()
        params.update(kwargs.get('params', {}))
        
        # Prepare headers
        headers = api_config.get('headers', {}).copy()
        headers.update(kwargs.get('headers', {}))
        
        # Check for required authentication
        requires_auth = 'api_key' in api_config or 'auth_required' in api_config
        
        return ApiEndpoint(
            name=name,
            url=url,
            method=api_config.get('method', 'GET'),
            params=params,
            headers=headers,
            description=api_config.get('description', ''),
            requires_auth=requires_auth
        )
    
    def make_request(self, api_id: str, params: Dict = None, endpoint_name: str = None) -> Optional[Dict]:
        """
        Make a request to the specified API endpoint
        
        Args:
            api_id: The ID of the API (e.g., 'wikipedia_de')
            params: Dictionary of parameters to include in the request
            endpoint_name: Optional endpoint name for APIs with multiple endpoints
            
        Returns:
            JSON response from the API or None if the request failed
        """
        if api_id not in self.apis:
            self.logger.error(f"API not found: {api_id}")
            return None
            
        api_config = self.apis[api_id]
        url = api_config.get('base_url', '')
        
        # Get default parameters and headers
        default_params = api_config.get('default_params', {})
        headers = api_config.get('headers', {})
        
        # Merge default params with provided params
        request_params = api_config.get('params', {}).copy()
        request_params.update(default_params)
        if params:
            request_params.update(params)
            
        # Replace placeholders in the URL with values from params
        if '{' in url and '}' in url:
            format_params = {k: v for k, v in request_params.items() if k in url}
            url = url.format(**format_params)
            
        # Handle endpoints if specified
        if endpoint_name and 'endpoints' in api_config and endpoint_name in api_config['endpoints']:
            endpoint = api_config['endpoints'][endpoint_name]
            if endpoint.startswith('http'):
                url = endpoint
            else:
                url = url.rstrip('/') + endpoint
            
        try:
            # Add default headers if not provided
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'J.A.R.V.I.S. Knowledge Collector (https://github.com/yourusername/jarvis)'
                
            self.logger.debug(f"Making request to {url} with params: {request_params}")
            response = requests.get(url, params=request_params, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Handle potential JSON decode errors with more detailed logging
            try:
                # Log the raw response for debugging
                response_text = response.text
                self.logger.debug(f"Raw API response (first 500 chars): {response_text[:500]}")
                
                # Try to parse the JSON
                result = response.json()
                self.logger.debug(f"Successfully parsed JSON response")
                return result
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {str(e)}")
                self.logger.error(f"Response status code: {response.status_code}")
                self.logger.error(f"Response headers: {dict(response.headers)}")
                self.logger.error(f"Response content (first 500 chars): {response.text[:500]}")
                return None
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" - {e.response.status_code} - {e.response.text[:200]}"
            self.logger.error(f"API request failed: {error_msg}")
            return None

# Example usage
if __name__ == "__main__":
    # Initialize the API manager
    api_manager = ApiManager()
    
    # List all available APIs
    print("Available APIs:")
    for api in api_manager.get_api_list():
        print(f"- {api['name']} ({api['id']}): {api['description']}")
    
    # Example: Search Wikipedia (German)
    try:
        print("\nSearching Wikipedia (DE) for 'Deutschland':")
        result = api_manager.make_request(
            'wikipedia_search',
            params={'q': 'Deutschland', 'lang': 'de'}
        )
        print(f"Found {result.get('query', {}).get('searchinfo', {}).get('totalhits', 0)} results")
        
        # Example: Get article summary
        print("\nGetting article summary for 'Deutschland':")
        result = api_manager.make_request(
            'wikipedia_de',
            endpoint_name='Deutschland'
        )
        print(f"Title: {result.get('title')}")
        print(f"Extract: {result.get('extract', '')[:200]}...")
        
        # Example: Get weather
        print("\nGetting weather for Berlin:")
        result = api_manager.make_request(
            'openweathermap',
            endpoint_name='weather',
            params={'q': 'Berlin,de', 'appid': 'YOUR_API_KEY'}
        )
        print(f"Weather in {result.get('name')}: {result.get('weather', [{}])[0].get('description')}")
        print(f"Temperature: {result.get('main', {}).get('temp')}°C")
        
    except Exception as e:
        print(f"Error: {str(e)}")
