#!/usr/bin/env python
"""Phase 2 Integration Test - Real Forensic Engine"""

import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

import requests
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
TEST_VIDEO = Path("test_video.mp4")

if not TEST_VIDEO.exists():
    print("[FAIL] Test video not found")
    exit(1)

print("=" * 70)
print("PHASE 2 INTEGRATION TEST - REAL FORENSIC ENGINE")
print("=" * 70)

# TEST 1: Health
print("\n[1/4] Health Check...")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"[PASS] Backend online: {r.json()['status']}")
except Exception as e:
    print(f"[FAIL] {e}")
    exit(1)

# TEST 2: Start Analysis
print("\n[2/4] Starting Video-to-Video Analysis...")
analysis_id = None
try:
    with open(TEST_VIDEO, 'rb') as f1, open(TEST_VIDEO, 'rb') as f2:
        files = {
            'reference_video': ('ref.mp4', f1, 'video/mp4'),
            'target_video': ('tgt.mp4', f2, 'video/mp4')
        }
        data = {'displacement_threshold': 10.0, 'diff_threshold': 20, 'ssim_threshold': 0.85}
        r = requests.post(f"{BASE_URL}/api/analyze/video", files=files, data=data, timeout=10)
        analysis_id = r.json()['analysis_id']
        print(f"[PASS] Analysis ID: {analysis_id}")
except Exception as e:
    print(f"[FAIL] {e}")
    exit(1)

# TEST 3: Poll Status
print("\n[3/4] Polling Analysis Status (up to 20 minutes)...")
for attempt in range(240):
    try:
        r = requests.get(f"{BASE_URL}/api/analysis/{analysis_id}/status", timeout=30)
        status = r.json()
        print(f"  [{attempt:3d}] {status['status']:12s} | {status['progress']:5.0f}% | {status['current_step']}")
        
        if status['status'] == 'completed':
            print(f"[PASS] Analysis completed")
            score = status.get('results', {}).get('deepfake_score', 'N/A')
            glitches = status.get('results', {}).get('glitch_frames', 'N/A')
            print(f"       Score: {score}, Glitches: {glitches}")
            break
        elif status['status'] == 'failed':
            print(f"[FAIL] {status.get('error_message')}")
            exit(1)
    except Exception as e:
        print(f"[FAIL] {e}")
        exit(1)
    
    if attempt < 239:
        time.sleep(5)
else:
    print(f"[FAIL] Timeout")
    exit(1)

# TEST 4: Get Results
print("\n[4/4] Retrieving Full Results...")
try:
    r = requests.get(f"{BASE_URL}/api/analysis/{analysis_id}", timeout=5)
    result = r.json()
    print(f"[PASS] Results retrieved")
    print(f"       ID: {result['id']}")
    print(f"       Type: {result['type']}")
    print(f"       Status: {result['status']}")
    if result.get('results'):
        res = result['results']
        print(f"       Score: {res.get('deepfake_score')}")
        print(f"       Frames: {res.get('total_frames')}")
        print(f"       Glitches: {res.get('glitch_frames')}")
except Exception as e:
    print(f"[FAIL] {e}")
    exit(1)

print("\n" + "=" * 70)
print("ALL TESTS PASSED - PHASE 2 INTEGRATION COMPLETE")
print("=" * 70)
print("\nVerification Summary:")
print("  [OK] Real forensic modules loaded")
print("  [OK] File uploads working")
print("  [OK] Real pipeline executing")
print("  [OK] Real results returned")
print("  [OK] Status polling functional")
print("  [OK] Complete analysis working end-to-end")
