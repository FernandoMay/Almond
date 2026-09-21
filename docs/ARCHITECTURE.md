# Architecture

The engine is a functional pipeline: deterministic scenario → demand calculation → full-open baseline and CP-SAT optimization → independent verification → economics and explanations → CLI JSON.

Domain dataclasses are immutable and do not depend on OR-Tools. Only `optimizer.py` imports CP-SAT. This keeps the verifier independent of solver decisions and makes model behavior testable. The optimization objective minimizes labor cost plus a large uncovered-demand penalty, subject to availability, contiguous daily intervals, and a 40-hour weekly cap.
