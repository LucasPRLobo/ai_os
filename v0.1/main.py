#!/usr/bin/env python3
"""
AI-OS Smart File Organizer
Main entry point for running the file organization pipeline.

Usage:
    python main.py /path/to/directory              # Analyze only
    python main.py /path/to/directory --execute    # Analyze, confirm, and move
    python main.py /path/to/directory --dry-run    # Preview what would happen
    python main.py --help
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

from models.state import create_initial_state
from graph.main_graph import create_organization_graph
from nodes.confirm_selection import confirm_selection, auto_confirm_first
from nodes.file_mover import execute_organization
from utils.progress import init_progress
from nodes.learning_node import learn_from_choice 


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AI-OS Smart File Organizer - Intelligent file organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py ~/Desktop              # Analyze and suggest
  python main.py ~/Desktop --execute    # Analyze, confirm, and organize
  python main.py ~/Desktop --dry-run    # Preview what would happen
  python main.py ~/Desktop -e -y        # Auto-accept first suggestion
  python main.py ~/Desktop -e --copy    # Copy instead of move
  python main.py . --model llama3.2     # Use specific model
        """
    )
    
    parser.add_argument(
        "paths",
        nargs="+",
        help="Files or directories to organize"
    )
    
    parser.add_argument(
        "--execute", "-e",
        action="store_true",
        help="Execute organization (move files after confirmation)"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Preview what would happen without moving files"
    )
    
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Auto-accept first suggestion (skip confirmation)"
    )
    
    parser.add_argument(
        "--copy", "-c",
        action="store_true",
        help="Copy files instead of moving them"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory for organized files"
    )
    
    parser.add_argument(
        "--model", "-m",
        default="llava:7b",
        help="Ollama model to use (default: llava:7b)"
    )
    
    parser.add_argument(
        "--no-recursive", "-nr",
        action="store_true",
        help="Don't scan directories recursively"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress output"
    )
    
    parser.add_argument(
        "--preview-length", "-p",
        type=int,
        default=1000,
        help="Max characters for text file previews (default: 1000)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    input_paths = []
    for path_str in args.paths:
        path = Path(path_str).expanduser().resolve()
        input_paths.append(str(path))
    
    # Initialize progress tracking
    tracker = init_progress(enabled=not args.quiet)
    
    # Print header
    if not args.quiet:
        print("\n" + "=" * 70)
        print("🗂️  AI-OS Smart File Organizer")
        print("=" * 70)
        print(f"\n📂 Input paths: {len(input_paths)}")
        for p in input_paths[:5]:
            print(f"   • {p}")
        if len(input_paths) > 5:
            print(f"   ... and {len(input_paths) - 5} more")
        
        mode = "ANALYZE ONLY"
        if args.dry_run:
            mode = "DRY RUN (preview)"
        elif args.execute:
            mode = "EXECUTE (will move files)"
        
        print(f"\n⚙️  Mode: {mode}")
        print(f"   Model: {args.model}")
        print(f"   Recursive: {not args.no_recursive}")
        if args.copy:
            print(f"   Action: COPY (originals preserved)")
        if args.output:
            print(f"   Output: {args.output}")
        print()
    
    # Create initial state
    initial_state = create_initial_state(
        input_paths=input_paths,
        llm_provider="ollama",
        llm_model=args.model,
        max_content_preview=args.preview_length,
        recursive=not args.no_recursive,
        dry_run=args.dry_run,
        use_copy=args.copy,
        output_dir=args.output
    )
    
    # Create and run analysis graph
    tracker.start()
    start_time = datetime.now()
    
    try:
        app = create_organization_graph()
        state = app.invoke(initial_state)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    tracker.finish()
    
    # Calculate analysis time
    analysis_time = (datetime.now() - start_time).total_seconds()
    
    # Display suggestions
    display_suggestions(state, quiet=args.quiet)
    
    # If execute mode, continue with confirm and act
    if args.execute or args.dry_run:
        # Check if we have suggestions
        if not state.get("suggestions") or not state["suggestions"].suggestions:
            print("\n❌ No suggestions to execute")
            sys.exit(1)
        
        # Confirm selection
        if args.yes:
            # Auto-accept first suggestion
            state = auto_confirm_first(state)
            if not args.quiet:
                sugg = state["selected_suggestion"]
                print(f"\n✓ Auto-selected: {sugg.folder_structure.base_path}")
        else:
            # Interactive confirmation
            state = confirm_selection(state)
        
        # Check if cancelled
        if state.get("user_cancelled"):
            print("\n👋 Operation cancelled")
            sys.exit(0)
        
        # Execute organization
        if state.get("selected_suggestion"):
            state = execute_organization(state)

        
            state = learn_from_choice(state)
            
            
            # Show execution result
            result = state.get("execution_result", {})
            if result.get("status") == "dry_run":
                print(f"\n✅ Dry run complete. Would {result.get('action', 'move')} {result.get('would_process', 0)} files.")
            elif result.get("status") == "success":
                print(f"\n✅ Organization complete!")
            elif result.get("status") == "partial":
                print(f"\n⚠️  Completed with some errors")
    else:
        # Analysis-only mode - show hint
        if not args.quiet and state.get("suggestions"):
            print("\n💡 To organize files, run again with --execute or -e")
    
    # Show total time
    total_time = (datetime.now() - start_time).total_seconds()
    if not args.quiet:
        print(f"\n⏱️  Total time: {total_time:.1f}s")
    
    # Return exit code
    if state.get("errors"):
        sys.exit(1)
    sys.exit(0)


def display_suggestions(state: dict, quiet: bool = False):
    """Display the organization suggestions."""
    print("\n" + "=" * 70)
    print("📊 ANALYSIS RESULTS")
    print("=" * 70)
    
    # Show errors first
    errors = state.get("errors", [])
    if errors:
        print("\n❌ ERRORS:")
        for error in errors:
            print(f"   • {error}")
    
    # Show file summary
    total_files = state.get("total_files_scanned", 0)
    total_size = state.get("total_size_bytes", 0)
    
    print(f"\n📁 Files analyzed: {total_files}")
    print(f"💾 Total size: {format_size(total_size)}")
    
    # Show classification breakdown
    image_files = state.get("image_files", [])
    text_files = state.get("text_files", [])
    document_files = state.get("document_files", [])
    other_files = state.get("other_files", [])
    
    if any([image_files, text_files, document_files, other_files]):
        print(f"\n📋 File types:")
        if image_files:
            print(f"   🖼️  Images: {len(image_files)}")
        if text_files:
            print(f"   📝 Text/Code: {len(text_files)}")
        if document_files:
            print(f"   📄 Documents: {len(document_files)}")
        if other_files:
            print(f"   📦 Other: {len(other_files)}")
    
    # Show suggestions
    suggestions = state.get("suggestions")
    if suggestions and suggestions.suggestions:
        print("\n" + "-" * 70)
        print("🎯 ORGANIZATION SUGGESTIONS")
        print("-" * 70)
        
        if hasattr(suggestions, 'analysis_summary') and suggestions.analysis_summary:
            print(f"\n📝 {suggestions.analysis_summary}")
        
        for i, sugg in enumerate(suggestions.suggestions, 1):
            confidence = sugg.confidence
            if confidence >= 0.8:
                conf_icon = "🟢"
            elif confidence >= 0.5:
                conf_icon = "🟡"
            else:
                conf_icon = "🔴"
            
            # Count total files
            total_assigned = sum(f.get_total_files() for f in sugg.folder_structure.folders)
            
            print(f"\n{conf_icon} Option {i}: {sugg.folder_structure.base_path}/")
            print(f"   Confidence: {confidence:.0%} | Files: {total_assigned}")
            print(f"   {sugg.reasoning}")
            
            # Show folder structure
            print(f"\n   Structure:")
            for folder in sugg.folder_structure.folders:
                file_count = folder.get_total_files()
                print(f"   📁 {folder.name}/ ({file_count} files)")
                
                # Show files
                for f in folder.files[:4]:
                    print(f"      • {f}")
                if len(folder.files) > 4:
                    print(f"      ... and {len(folder.files) - 4} more")
    else:
        if not errors:
            print("\n⚠️  No suggestions generated")
    
    print("\n" + "=" * 70)


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    if size_bytes is None:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


if __name__ == "__main__":
    main()