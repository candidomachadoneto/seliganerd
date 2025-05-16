import os
import subprocess
from pathlib import Path
from datetime import date
import pandas as pd
import sys


def test_csv_created():
    env = os.environ.copy()
    env['GLEISI_TWEETS_FAKE'] = '1'
    subprocess.run([sys.executable, 'scripts/gleisi_tweets.py'], check=True, env=env)
    csv_path = Path('data') / f'gleisi_selic_{date.today().isoformat()}.csv'
    assert csv_path.exists(), 'CSV file not created'
    df = pd.read_csv(csv_path)
    assert len(df) >= 1, 'CSV should contain at least one tweet'
