#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tortsignal/src'))

from db import get_cursor

with get_cursor() as cur:
    # Get top candidates by score
    cur.execute('''
        SELECT defendant_text, product_text, injury_text, score_total, metrics_json
        FROM candidates
        ORDER BY score_total DESC
        LIMIT 20
    ''')

    print('Top 20 candidates in database by score:')
    print('='*80)
    for row in cur.fetchall():
        product = row['product_text']
        injury = row['injury_text']
        score = row['score_total']
        metrics = row['metrics_json']

        signal = metrics.get('signal_metadata', {})
        baseline = signal.get('baseline_count', 0)
        recent = signal.get('recent_count', 0)
        velocity = signal.get('velocity', 0)
        total = signal.get('total_count', 0)

        print(f'{product:25s} [{injury:15s}] Score: {score:5.1f}')
        print(f'  Total: {total:,} | Baseline: {baseline} → Recent: {recent} ({velocity:+.1f}%)')
        print()
