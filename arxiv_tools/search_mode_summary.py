#!/usr/bin/env python3
"""
Summary of search mode performance for the standalone arXiv discovery script.
"""

def print_search_summary():
    """Print a summary of how different search modes perform."""
    
    print(" ArXiv Discovery Search Mode Performance Summary")
    print("=" * 70)
    print()
    
    search_modes = [
        {
            "mode": "boolean",
            "query_example": "foundational model AND robotics",
            "results": "24,940",
            "note": "Too broad - treats as simple boolean logic"
        },
        {
            "mode": "phrase", 
            "query_example": 'all:"foundational model" AND all:robotics',
            "results": "609",
            "note": "Exact phrase matching - conservative but accurate"
        },
        {
            "mode": "web-like",
            "query_example": 'all:"foundational model" AND all:robotics', 
            "results": "609",
            "note": "Same as phrase mode - mimics web interface behavior"
        },
        {
            "mode": "split-terms",
            "query_example": "all:foundational AND all:model AND all:robotics",
            "results": "1,107",
            "note": "⭐ RECOMMENDED - Closest to web interface (~927)"
        },
        {
            "mode": "compound-terms", 
            "query_example": "all:foundational AND all:model AND all:robotics",
            "results": "1,107", 
            "note": "⭐ RECOMMENDED - Same as split-terms for target query"
        },
        {
            "mode": "user-format",
            "query_example": "all:foundational AND all:model AND all:robotics", 
            "results": "1,107",
            "note": "Same behavior as split-terms/compound-terms"
        },
        {
            "mode": "title-phrase",
            "query_example": 'ti:"foundational model" AND all:robotics',
            "results": "65",
            "note": "Very precise - only searches titles"
        },
        {
            "mode": "precise",
            "query_example": 'abs:"foundational model" AND all:robotics',
            "results": "468", 
            "note": "Searches abstracts specifically"
        }
    ]
    
    print("Query: 'foundational model AND robotics'")
    print("Target (arXiv web interface): ~927 results")
    print()
    
    for mode_info in search_modes:
        print(f" {mode_info['mode'].upper():<15} | {mode_info['results']:>6} results")
        print(f"   Query: {mode_info['query_example']}")
        print(f"   Note:  {mode_info['note']}")
        print()
    
    print(" RECOMMENDATIONS:")
    print("   • For best match to web interface: use 'split-terms' or 'compound-terms'")
    print("   • For conservative/precise results: use 'phrase' or 'title-phrase'") 
    print("   • For very broad discovery: use 'boolean' (but expect many false positives)")
    print()
    
    print(" QUERY CONSTRUCTION LOGIC:")
    print("   • 'split-terms': Splits multi-word terms into separate 'all:word' searches")
    print("   • 'phrase': Uses quoted phrases for exact matching")
    print("   • 'boolean': Uses default arXiv API boolean logic")
    print("   • The arXiv API doesn't handle 'all:foundational+model' well")
    print("   • Splitting into individual words gives better coverage")

if __name__ == "__main__":
    print_search_summary()
