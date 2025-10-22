#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test database connection"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "aide-data-core"))

from aide_data_core.models import get_engine, get_session, NaverNews

# Test database path
db_path = str(project_root / "aide-data-core" / "aide_dev.db").replace("\\", "/")
db_url = f"sqlite:///{db_path}"

print(f"DB Path: {db_path}")
print(f"DB URL: {db_url}")
print(f"File exists: {(project_root / 'aide-data-core' / 'aide_dev.db').exists()}")
print()

# Try to connect
try:
    engine = get_engine(db_url)
    session = get_session(engine)

    # Try a simple query
    count = session.query(NaverNews).count()
    print(f"Successfully connected to database!")
    print(f"Number of NaverNews records: {count}")

    session.close()
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
