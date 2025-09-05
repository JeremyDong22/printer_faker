# Task Completion Checklist

## When Completing Any Task

### 1. Testing (MANDATORY - TDD)
```bash
# Run tests to ensure nothing is broken
uv run python3 -m pytest tests/ -v

# If tests don't exist yet, create them first!
# Remember: RED-GREEN-REFACTOR cycle
```

### 2. Code Quality Checks
Since no specific linting/formatting tools are configured yet, ensure:
- Code follows the style conventions in CLAUDE.md
- Functions have clear type hints
- Error messages are descriptive
- No unnecessary complexity

### 3. Verification Steps
```bash
# Test the setup
uv run python3 test_setup.py  # If exists

# Run the application to verify it works
uv run python3 virtual_printer.py  # For main service
uv run python3 printer_api_service.py  # For API service
```

### 4. Documentation
- Update docstrings if you changed function behavior
- Ensure code is self-documenting with clear variable names
- Add comments only for complex logic that isn't obvious

### 5. Git Hygiene
```bash
# Check what changed
git status
git diff

# Stage and commit with clear message
git add <files>
git commit -m "Clear, descriptive commit message"

# DO NOT push unless explicitly asked by user
```

## Specific Checks by Task Type

### For New Features
1. Write failing test first (RED)
2. Implement minimal code to pass (GREEN)
3. Refactor for clarity (REFACTOR)
4. Verify all existing tests still pass
5. Update documentation if needed

### For Bug Fixes
1. Write a test that reproduces the bug
2. Fix the bug
3. Verify the test now passes
4. Run all tests to ensure no regression

### For Refactoring
1. Ensure tests exist and pass before refactoring
2. Make changes
3. Run tests to verify behavior unchanged
4. Check performance hasn't degraded

## Commands to Run Before Considering Task Complete

```bash
# 1. Run all tests (if they exist)
uv run python3 -m pytest tests/ -v

# 2. Try to run the main application
uv run python3 virtual_printer.py

# 3. Check for syntax errors in all Python files
uv run python3 -m py_compile virtual_printer.py
uv run python3 -m py_compile printer_api_service.py

# 4. Verify imports work
uv run python3 -c "import virtual_printer"
```

## Red Flags - Task NOT Complete If:
- Tests are failing
- Application won't start
- Import errors exist
- Syntax errors present
- Type hints missing on new functions
- No tests written for new code (TDD violation)
- Error handling missing for edge cases

## Final Verification Question
Ask yourself: "Would another developer be able to understand and maintain this code without my help?"

If the answer is no, the task needs more work on clarity and documentation.