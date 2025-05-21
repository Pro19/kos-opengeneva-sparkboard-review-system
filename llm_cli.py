"""
CLI utility for selecting and testing different LLM providers.
"""

import argparse
import json
import sys
from config import LLM_CONFIG
from llm_interface import generate_llm_response

def update_config_provider(provider: str) -> None:
    """
    Update the default LLM provider in the config file.
    
    Args:
        provider: The provider to set as default ("claude", "chatgpt", "ollama", or "grok")
    """
    if provider not in ["claude", "chatgpt", "ollama", "grok"]:
        print(f"Error: Invalid provider '{provider}'. Choose from: claude, chatgpt, ollama, grok")
        return
    
    # Update the config file
    import os
    config_path = os.path.join(os.path.dirname(__file__), "config.py")
    
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config_content = f.read()
        
        # Replace the provider line
        config_content = config_content.replace(
            f'"provider": "{LLM_CONFIG.get("provider", "ollama")}"',
            f'"provider": "{provider}"'
        )
        
        with open(config_path, "w") as f:
            f.write(config_content)
        
        print(f"Default LLM provider updated to: {provider}")
    else:
        print(f"Error: Config file not found at {config_path}")

def test_provider(provider: str, prompt: str = None) -> None:
    """
    Test a specific LLM provider with a sample prompt.
    
    Args:
        provider: The provider to test ("claude", "chatgpt", or "ollama")
        prompt: Optional custom prompt to use
    """
    if provider not in ["claude", "chatgpt", "ollama", "grok"]:
        print(f"Error: Invalid provider '{provider}'. Choose from: claude, chatgpt, ollama, grok")
        return
    
    # Use default prompt if none provided
    if prompt is None:
        prompt = "Explain the concept of ontology in knowledge representation in one paragraph."
    
    print(f"Testing {provider.upper()} LLM provider with prompt: '{prompt}'")
    print("-" * 80)
    
    try:
        response = generate_llm_response(prompt, provider)
        print(f"Response from {provider.upper()}:")
        print("-" * 80)
        print(response)
        print("-" * 80)
        print("Test completed successfully!")
    except Exception as e:
        print(f"Error testing {provider}: {str(e)}")

def print_current_config() -> None:
    """Print the current LLM configuration."""
    print("Current LLM Configuration:")
    print("-" * 80)
    print(f"Default Provider: {LLM_CONFIG.get('provider', 'ollama')}")
    
    for provider, config in LLM_CONFIG.items():
        if provider != "provider":
            print(f"\n{provider.upper()} Configuration:")
            for key, value in config.items():
                if key == "api_key":
                    value = "****" if value != "YOUR_API_KEY" else value
                print(f"  {key}: {value}")
    
    print("-" * 80)

def main() -> None:
    """Main entry point for the CLI utility."""
    parser = argparse.ArgumentParser(description="LLM Provider Management Utility")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Command to get current config
    config_parser = subparsers.add_parser("config", help="Show current LLM configuration")
    
    # Command to set default provider
    set_parser = subparsers.add_parser("set", help="Set default LLM provider")
    set_parser.add_argument("provider", choices=["claude", "chatgpt", "ollama", "grok"], 
                        help="Provider to set as default")

    # Command to test a provider
    test_parser = subparsers.add_parser("test", help="Test an LLM provider")
    test_parser.add_argument("provider", choices=["claude", "chatgpt", "ollama", "grok"], 
                            help="Provider to test")
    test_parser.add_argument("--prompt", help="Custom prompt to use for testing")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "config":
        print_current_config()
    elif args.command == "set":
        update_config_provider(args.provider)
    elif args.command == "test":
        test_provider(args.provider, args.prompt)
    else:
        # Default to showing help if no command specified
        parser.print_help()

if __name__ == "__main__":
    main()