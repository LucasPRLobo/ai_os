#!/usr/bin/env python3
"""
AI-OS Natural Language File Search
Search files using natural language queries powered by local embeddings.

Usage:
    python -m skills.search index ~/Documents          # Build/update index
    python -m skills.search query "meeting notes"      # Search with natural language
    python -m skills.search query "photos" --type image # Filter by type
    python -m skills.search stats                       # Show index statistics
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

from shared.providers.embedding import OllamaEmbeddingProvider
from shared.learning.embedding_store import EmbeddingStore
from skills.search.graph.search_graph import create_index_graph, create_search_graph


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AI-OS Natural Language File Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m skills.search index ~/Documents                # Index a directory
  python -m skills.search query "meeting notes about budget" # Search
  python -m skills.search query "python scripts" --type code # Filter by type
  python -m skills.search query "beach photos" --type image  # Filter images
  python -m skills.search stats                              # Show stats
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Index command
    index_parser = subparsers.add_parser("index", help="Index files for search")
    index_parser.add_argument(
        "paths",
        nargs="+",
        help="Directories or files to index"
    )
    index_parser.add_argument(
        "--no-recursive", "-nr",
        action="store_true",
        help="Don't scan directories recursively"
    )

    # Query command
    query_parser = subparsers.add_parser("query", help="Search with natural language")
    query_parser.add_argument(
        "query",
        help="Natural language search query"
    )
    query_parser.add_argument(
        "--type", "-t",
        choices=["image", "text", "code", "document", "audio", "video"],
        default=None,
        help="Filter results by file type"
    )
    query_parser.add_argument(
        "--top", "-k",
        type=int,
        default=10,
        help="Number of results to show (default: 10)"
    )
    query_parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help="Minimum similarity threshold (default: 0.3)"
    )

    # Stats command
    subparsers.add_parser("stats", help="Show index statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "index":
        _run_index(args)
    elif args.command == "query":
        _run_query(args)
    elif args.command == "stats":
        _run_stats()


def _run_index(args):
    """Run the indexing pipeline."""
    # Check embedding provider
    provider = OllamaEmbeddingProvider()
    if not provider.is_available():
        print("\n  Ollama is not running or nomic-embed-text is not installed.")
        print("  Please start Ollama and install the model:")
        print("    ollama serve")
        print("    ollama pull nomic-embed-text")
        sys.exit(1)

    # Resolve paths
    input_paths = []
    for path_str in args.paths:
        path = Path(path_str).expanduser().resolve()
        if not path.exists():
            print(f"  Path does not exist: {path_str}")
            continue
        input_paths.append(str(path))

    if not input_paths:
        print("  No valid paths to index")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  AI-OS File Search - Indexing")
    print("=" * 60)
    print(f"\n  Paths: {len(input_paths)}")
    for p in input_paths[:5]:
        print(f"    - {p}")
    print(f"  Recursive: {not args.no_recursive}")
    print()

    # Run index graph
    start_time = datetime.now()

    try:
        app = create_index_graph()
        state = app.invoke({
            "input_paths": input_paths,
            "recursive": not args.no_recursive,
            "errors": [],
            "warnings": [],
        })
    except KeyboardInterrupt:
        print("\n  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n  Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    elapsed = (datetime.now() - start_time).total_seconds()

    # Show results
    indexed = state.get("files_indexed", 0)
    skipped = state.get("files_skipped", 0)
    errors = state.get("errors", [])

    print(f"\n  Indexing complete in {elapsed:.1f}s")
    print(f"  Files indexed: {indexed}")
    if skipped:
        print(f"  Files skipped (already indexed): {skipped}")
    if errors:
        print(f"\n  Errors:")
        for err in errors[:5]:
            print(f"    - {err}")

    print()


def _run_query(args):
    """Run a search query."""
    store = EmbeddingStore()
    stats = store.get_stats()

    if stats["total_files"] == 0:
        print("\n  No files indexed yet. Run 'index' first:")
        print("    python -m skills.search index ~/Documents")
        sys.exit(1)

    # Check embedding provider
    provider = OllamaEmbeddingProvider()
    if not provider.is_available():
        print("\n  Ollama is not running or nomic-embed-text is not installed.")
        sys.exit(1)

    print(f"\n  Searching for: \"{args.query}\"")
    if args.type:
        print(f"  Filter: {args.type}")
    print()

    start_time = datetime.now()

    try:
        app = create_search_graph()
        state = app.invoke({
            "query": args.query,
            "content_type_filter": args.type,
            "top_k": args.top,
            "threshold": args.threshold,
            "errors": [],
        })
    except Exception as e:
        print(f"  Error: {e}")
        sys.exit(1)

    elapsed = (datetime.now() - start_time).total_seconds()

    # Display results
    results = state.get("results", [])
    if not results:
        print("  No matching files found.")
    else:
        print(f"  Found {len(results)} results ({elapsed:.2f}s):\n")
        print("-" * 70)

        for i, result in enumerate(results, 1):
            score = result["score"]
            file_path = result["file_path"]
            file_name = result["file_name"]
            content_type = result.get("content_type", "unknown")
            summary = result.get("content_summary", "")

            # Confidence color indicator
            if score >= 0.7:
                conf = "[HIGH]"
            elif score >= 0.5:
                conf = "[MED]"
            else:
                conf = "[LOW]"

            print(f"  {i}. {conf} {file_name}  ({score:.0%})")
            print(f"     Type: {content_type}")
            print(f"     Path: {file_path}")
            if summary:
                # Truncate summary
                if len(summary) > 100:
                    summary = summary[:97] + "..."
                print(f"     {summary}")
            print()

    print("-" * 70)
    print(f"  {len(results)} results | Index: {stats['total_files']} files | {elapsed:.2f}s")
    print()


def _run_stats():
    """Show index statistics."""
    store = EmbeddingStore()
    stats = store.get_stats()

    print("\n" + "=" * 50)
    print("  AI-OS Search Index Statistics")
    print("=" * 50)

    print(f"\n  Total files indexed: {stats['total_files']}")
    print(f"  Database size: {stats['database_size_human']}")
    print(f"  Last indexed: {stats['last_indexed'] or 'Never'}")

    if stats["type_breakdown"]:
        print(f"\n  File types:")
        for ftype, count in sorted(stats["type_breakdown"].items(), key=lambda x: -x[1]):
            print(f"    {ftype or 'unknown'}: {count}")

    print()


if __name__ == "__main__":
    main()
