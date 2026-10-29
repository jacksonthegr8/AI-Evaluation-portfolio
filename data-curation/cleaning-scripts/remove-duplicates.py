#!/usr/bin/env python3
"""
remove-duplicates.py
Production-ready JSONL deduplication script with streaming, error recovery,
and field-specific key support. Designed for AI dataset curation workflows.

Author: Kanu Jackson Chimeremeze 
Date: July 2024
"""

import json
import sys
import argparse
from pathlib import Path
from collections import OrderedDict


def deduplicate_jsonl(input_path, output_path, key_field=None, skip_errors=True):
    """
    Remove duplicate records from a JSONL file while preserving first-seen order.
    
    Args:
        input_path (str): Source JSONL file path
        output_path (str): Cleaned output file path
        key_field (str, optional): JSON field to use as dedup key (e.g., 'id', 'prompt_id')
        skip_errors (bool): If True, skip malformed lines instead of crashing
    
    Returns:
        dict: Statistics {'total': int, 'unique': int, 'duplicates': int, 'errors': int}
    """
    seen = OrderedDict()
    stats = {"total": 0, "unique": 0, "duplicates": 0, "errors": 0}
    
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        for line_num, raw_line in enumerate(infile, 1):
            stats["total"] += 1
            line = raw_line.strip()
            
            if not line:
                continue
            
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                stats["errors"] += 1
                if skip_errors:
                    print(f"[Warning] Line {line_num}: JSON parse error. Skipping. ({e})")
                    continue
                else:
                    raise ValueError(f"Line {line_num}: Invalid JSON") from e
            
            # Build deduplication key
            if key_field:
                # Use specific field; fallback to full record if field missing
                dup_key = record.get(key_field, f"__missing_key_field__:{line_num}")
            else:
                # Deterministic serialization of entire record
                dup_key = json.dumps(record, sort_keys=True, ensure_ascii=False)
            
            if dup_key in seen:
                stats["duplicates"] += 1
            else:
                seen[dup_key] = record
    
    # Write clean output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for record in seen.values():
            outfile.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    stats["unique"] = len(seen)
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Remove duplicate records from JSONL datasets"
    )
    parser.add_argument("input", help="Input JSONL file path")
    parser.add_argument("output", help="Output JSONL file path")
    parser.add_argument(
        "--key", "-k", 
        dest="key_field",
        help="Field name to use for deduplication (e.g., 'id', 'query_id')"
    )
    parser.add_argument(
        "--strict", 
        action="store_true",
        help="Crash on malformed JSON instead of skipping"
    )
    
    args = parser.parse_args()
    
    try:
        stats = deduplicate_jsonl(
            args.input, 
            args.output, 
            key_field=args.key_field,
            skip_errors=not args.strict
        )
        
        print("\n" + "=" * 40)
        print("DEDUPLICATION COMPLETE")
        print("=" * 40)
        print(f"Total lines read:     {stats['total']}")
        print(f"Unique records kept:  {stats['unique']}")
        print(f"Duplicates removed:   {stats['duplicates']}")
        print(f"Errors skipped:       {stats['errors']}")
        print(f"Output saved to:      {args.output}")
        print("=" * 40)
        
    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()