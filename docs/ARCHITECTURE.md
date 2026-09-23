# Architecture

The engine is a functional pipeline: deterministic scenario → demand calculation → explicit fixed-floor baseline and CP-SAT optimization → independent verification → economics and explanations → CLI JSON.

Domain dataclasses are immutable and do not depend on OR-Tools. Only `optimizer.py` imports CP-SAT. This keeps the verifier independent of solver decisions and makes model behavior testable. The optimization objective uses explicit labor, normal-shortage, and peak-shortage weights, subject to availability, contiguous daily intervals, explicit peak coverage, and a hard 40-hour weekly cap.
