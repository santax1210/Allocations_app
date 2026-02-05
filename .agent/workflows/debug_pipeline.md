---
description: Run the pipeline debug script and analyze logs
---

1. Run the debug pipeline script
// turbo
```bash
python src/debug_pipeline.py
```

2. Check for errors in the log file
```bash
grep "ERROR" pipeline_debug.log
```

3. Search for "Shape:" to see data flow volume
```bash
grep "Shape:" pipeline_debug.log
```

4. View the last 50 lines of the log to see the final result
```bash
tail -n 50 pipeline_debug.log
```
