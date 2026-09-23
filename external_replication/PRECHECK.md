# Precheck before an external run

1. Confirm the environment is genuinely independent of the MRSP development/confirmation panel.
2. Freeze the 53-week study period and all six-SKU group definitions before reading evaluation outcomes.
3. Preserve the original `events.csv` and `groups.csv` immutably; their SHA-256 hashes are written to output.
4. Run `python qa/make_fixture.py` and the fixture command first to verify the local Python environment.
5. Run `python qa/test_no_current_label_leak.py`.
6. Do not edit cutoffs, lambda grid, W1-W6 windows, or P1 formula.
7. If the strict runner fails, preserve the failure. Do not silently clean data based on result quality.
8. A program `PASS` means protocol execution succeeded, **not** that MRSP scientifically replicated.
