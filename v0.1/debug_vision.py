#!/usr/bin/env python3
"""
Debug Vision Analysis
Shows exactly what LLaVA is detecting in each image.
"""

import sys
from pathlib import Path
from datetime import datetime

from models.state import create_initial_state
from nodes.input_validator import validate_input
from nodes.file_scanner import scan_files
from nodes.metadata_extractor import extract_metadata
from nodes.classify_files import classify_files
from nodes.analyze_image import analyze_images


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_vision.py /path/to/images")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    print("=" * 70)
    print("🔍 VISION ANALYSIS DEBUG")
    print("=" * 70)
    print(f"\nAnalyzing: {input_path}\n")
    
    # Create state and run through pipeline up to image analysis
    state = create_initial_state(
        input_paths=[input_path],
        llm_provider="ollama",
        recursive=True
    )
    
    # Run nodes
    print("1. Validating input...")
    state = validate_input(state)
    if state.get("errors"):
        print(f"   ❌ Errors: {state['errors']}")
        return
    print("   ✓ OK")
    
    print("2. Scanning files...")
    state = scan_files(state)
    print(f"   ✓ Found {state.get('total_files_scanned', 0)} files")
    
    print("3. Extracting metadata...")
    state = extract_metadata(state)
    print(f"   ✓ Processed {len(state.get('files', []))} files")
    
    print("4. Classifying files...")
    state = classify_files(state)
    image_count = len(state.get("image_files", []))
    print(f"   ✓ Found {image_count} images")
    
    if image_count == 0:
        print("\n⚠️  No images found!")
        return
    
    print("\n5. Running vision analysis (this may take a while)...")
    print("-" * 70)
    
    state = analyze_images(state)
    
    image_analysis = state.get("image_analysis", [])
    
    print("\n" + "=" * 70)
    print("📸 VISION ANALYSIS RESULTS")
    print("=" * 70)
    
    if not image_analysis:
        print("\n⚠️  No vision analysis results!")
        print("   Check if LLaVA is installed: ollama list")
        print("   Install with: ollama pull llava:7b")
        return
    
    for i, img in enumerate(image_analysis, 1):
        print(f"\n{'─' * 70}")
        print(f"IMAGE {i}: {img.file_name}")
        print(f"{'─' * 70}")
        
        print(f"\n📝 DESCRIPTION:")
        print(f"   {img.description or 'No description'}")
        
        print(f"\n🏷️  OBJECTS DETECTED:")
        if img.objects:
            print(f"   {', '.join(img.objects)}")
        else:
            print("   None detected")
        
        print(f"\n🎬 SCENE TYPE: {img.scene_type or 'Unknown'}")
        print(f"🏠 INDOOR/OUTDOOR: {img.indoor_outdoor or 'Unknown'}")
        print(f"👥 PEOPLE COUNT: {img.people_count if img.people_count is not None else 'Unknown'}")
        
        if img.activities:
            print(f"🎯 ACTIVITIES: {', '.join(img.activities)}")
        
        if img.location_from_exif:
            print(f"📍 LOCATION (EXIF): {img.location_from_exif}")
        
        if img.date_taken:
            print(f"📅 DATE TAKEN: {img.date_taken.strftime('%Y-%m-%d %H:%M')}")
        
        if img.camera_model:
            camera = f"{img.camera_make or ''} {img.camera_model}".strip()
            print(f"📷 CAMERA: {camera}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    scenes = {}
    for img in image_analysis:
        scene = img.scene_type or "unknown"
        scenes[scene] = scenes.get(scene, 0) + 1
    
    print(f"\nTotal images analyzed: {len(image_analysis)}")
    print(f"\nScene distribution:")
    for scene, count in sorted(scenes.items(), key=lambda x: -x[1]):
        print(f"   {scene}: {count}")
    
    # Show any warnings
    if state.get("warnings"):
        print(f"\n⚠️  Warnings:")
        for w in state["warnings"]:
            print(f"   - {w}")


if __name__ == "__main__":
    main()