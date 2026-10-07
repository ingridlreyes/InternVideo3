#!/usr/bin/env python3
"""
Validate and summarize a locally downloaded ALEX-GYM-1 dataset.

This script NEVER fabricates missing rows or labels. It stops if the expected
files are absent or inconsistent.

Expected author layout:
  squat.xlsx
  deadlift.xlsx
  lunges.xlsx
  front_pose_squat.json
  lat_pose_squat.json
  front_pose_deadlift.json
  lat_pose_deadlift.json
  front_pose_lunges.json
  lat_pose_lunges.json
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

ACTIONS=("squat","deadlift","lunges")

def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def summarize(base: Path) -> dict:
    out={"dataset":"ALEX-GYM-1","actions":{},"total_rows":0}
    for action in ACTIONS:
        xlsx=base/f"{action}.xlsx"
        front=base/f"front_pose_{action}.json"
        lat=base/f"lat_pose_{action}.json"
        for p in (xlsx,front,lat):
            if not p.exists():
                raise FileNotFoundError(p)
        df=pd.read_excel(xlsx)
        f=load_json(front); l=load_json(lat)
        if len(df)!=len(f) or len(df)!=len(l):
            raise ValueError(f"{action}: metadata/pose row count mismatch: xlsx={len(df)} front={len(f)} lateral={len(l)}")

        rating_cols=[c for c in df.columns if str(c).endswith("F") or str(c).endswith("L")]
        action_info={
            "rows":int(len(df)),
            "columns":[str(c) for c in df.columns],
            "rating_columns":[str(c) for c in rating_cols],
            "front_pose_rows":len(f),
            "lateral_pose_rows":len(l),
        }
        if rating_cols:
            prevalence={}
            for c in rating_cols:
                s=pd.to_numeric(df[c],errors="coerce")
                prevalence[str(c)]={"observed_n":int(s.notna().sum()),"mean":float(s.mean()) if s.notna().any() else None}
            action_info["rating_prevalence"]=prevalence
        out["actions"][action]=action_info
        out["total_rows"]+=len(df)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data-dir",required=True)
    ap.add_argument("--output",default="alex_gym_1_local_summary.json")
    args=ap.parse_args()
    summary=summarize(Path(args.data_dir))
    Path(args.output).write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
