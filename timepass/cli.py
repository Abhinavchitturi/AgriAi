#!/usr/bin/env python3
"""
Command Line Interface for Member A's NLP + Language Layer
Allows users to input queries in terminal and get results directly
"""

import argparse
import json
import sys
from typing import Dict, Any
from src.nlp_processor import NLPProcessor

def print_separator():
    """Print a separator line"""
    print("=" * 80)

def print_result(result: Dict[str, Any]):
    """Print formatted result"""
    print_separator()
    print("🔍 NLP PROCESSING RESULTS")
    print_separator()
    
    # Original Query
    print(f"📝 Original Query: {result.get('original_query', 'N/A')}")
    print()
    
    # Language Detection
    lang_detection = result.get('language_detection', {})
    print(f"🌍 Language Detection:")
    print(f"   • Detected Language: {lang_detection.get('language_name', 'Unknown')}")
    print(f"   • Language Code: {lang_detection.get('detected_language', 'unknown')}")
    print(f"   • Confidence: {lang_detection.get('confidence', 0.0):.3f}")
    print()
    
    # Translation
    translation = result.get('translation', {})
    print(f"🔄 Translation:")
    print(f"   • Translated Text: {translation.get('translated_text', 'N/A')}")
    print(f"   • Method: {translation.get('method', 'unknown')}")
    print(f"   • Confidence: {translation.get('confidence', 0.0):.3f}")
    print()
    
    # Intent Extraction
    intent_extraction = result.get('intent_extraction', {})
    print(f"🎯 Intent Extraction:")
    print(f"   • Detected Intent: {intent_extraction.get('intent', 'unknown')}")
    print(f"   • Confidence: {intent_extraction.get('confidence', 0.0):.3f}")
    print(f"   • Method: {intent_extraction.get('method', 'unknown')}")
    print()
    
    # Entity Extraction
    entity_extraction = result.get('entity_extraction', {})
    entities = entity_extraction.get('entities', {})
    print(f"🏷️  Entity Extraction:")
    if entities:
        for entity_type, entity_list in entities.items():
            print(f"   • {entity_type.title()}: {', '.join(entity_list)}")
    else:
        print("   • No entities detected")
    print()
    
    # Processing Metadata
    metadata = result.get('processing_metadata', {})
    print(f"⏱️  Processing Info:")
    print(f"   • Processing Time: {metadata.get('processing_time_seconds', 0.0):.3f} seconds")
    print(f"   • Pipeline Version: {metadata.get('pipeline_version', '1.0.0')}")
    print()
    
    # Cleaned Query (for downstream processing)
    cleaned_query = result.get('cleaned_query', '')
    if cleaned_query:
        print(f"🧹 Cleaned Query (for Member B):")
        print(f"   {cleaned_query}")
        print()
    
    # Error handling
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        print()
    
    print_separator()

def interactive_mode():
    """Run in interactive mode - continuously ask for queries"""
    processor = NLPProcessor()
    
    print("🚀 Member A: NLP + Language Layer - Interactive Mode")
    print("Enter queries in any language. Type 'quit' or 'exit' to stop.")
    print_separator()
    
    while True:
        try:
            # Get user input
            query = input("\n💬 Enter your query: ").strip()
            
            # Check for exit commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Skip empty queries
            if not query:
                print("⚠️  Please enter a valid query.")
                continue
            
            # Process the query
            print(f"\n🔄 Processing: {query}")
            result = processor.process_query(query)
            
            # Print results
            print_result(result)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error processing query: {e}")
            print("Please try again.")

def single_query_mode(query: str):
    """Process a single query"""
    processor = NLPProcessor()
    
    print(f"🔄 Processing: {query}")
    result = processor.process_query(query)
    print_result(result)

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Member A: NLP + Language Layer CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py -i                    # Interactive mode
  python cli.py "Hello, how are you?" # Single query
  python cli.py "नमस्ते, कैसे हो?"     # Hindi query
  python cli.py "¿Cómo estás?"        # Spanish query
        """
    )
    
    parser.add_argument(
        'query', 
        nargs='?', 
        help='Query to process (optional if using interactive mode)'
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '-j', '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    
    args = parser.parse_args()
    
    # Check if we have a query or interactive mode
    if args.interactive:
        interactive_mode()
    elif args.query:
        processor = NLPProcessor()
        result = processor.process_query(args.query)
        
        if args.json:
            # JSON output
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # Formatted output
            print_result(result)
    else:
        # No query provided and not interactive
        print("❌ Please provide a query or use interactive mode (-i)")
        print("Use -h for help.")
        sys.exit(1)

if __name__ == "__main__":
    main() 