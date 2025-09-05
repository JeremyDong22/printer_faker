# Code Style and Conventions

## Core Philosophy
**"Keep things as simple as possible, but not simpler"** - Einstein

## Test-Driven Development (TDD) - MANDATORY
### Red-Green-Refactor Cycle
1. **RED**: Write a failing test first
2. **GREEN**: Write minimal code to pass the test
3. **REFACTOR**: Clean up while keeping tests green

### TDD Rules
1. Never write production code without a failing test
2. Write only enough test code to fail
3. Write only enough production code to pass
4. Refactor only when tests are green
5. One test, one assertion (when possible)

### Test Structure
```python
def test_should_parse_bold_command():
    """Test name describes expected behavior"""
    # Arrange
    parser = ESCPOSParser()
    data = b'\x1B\x45\x01'
    
    # Act
    result = parser.parse(data)
    
    # Assert
    assert result == [('BOLD', True)]
```

## Implementation Guidelines

### 1. Single Responsibility
- Each class/function does ONE thing well
- ESCPOSParser only parses, doesn't handle I/O
- PrinterEmulator only manages connections, doesn't parse

### 2. Explicit Over Implicit
```python
# Good: Clear, explicit
def save_print_job(self, data: bytes, timestamp: str) -> str:
    filename = f"pos_print_{timestamp}.txt"
    
# Bad: Implicit, unclear
def save(self, d):
    f = f"pj_{time.time()}.txt"
```

### 3. Fail Fast, Fail Clearly
- Always validate early with clear error messages
- Example: `raise ValueError(f"Invalid Bluetooth address: {addr}")`

### 4. No Premature Optimization
- Start with simple, readable code
- Profile before optimizing
- Document any necessary complexity

### 5. Minimal Dependencies
- Only pybluez2 for Bluetooth functionality
- Standard library for everything else
- No unnecessary abstractions

### 6. Clear State Management
- State should be obvious and tracked
- Example:
  ```python
  self.is_connected = False
  self.current_job = None
  self.print_queue = queue.Queue()
  ```

## Design Pattern: Simple Event Loop
Single-threaded blocking architecture:
```python
while True:
    connection = wait_for_connection()  # Blocking
    while connection.is_active():
        data = receive_data()            # Blocking
        process_and_save(data)
        send_acknowledgment()
```

## Naming Conventions
- Test files: `tests/test_*.py`
- Test classes: `Test*`
- Test functions: `test_should_*` or `test_*`
- Clear, descriptive variable names
- Type hints for function parameters and returns

## Best Practices
1. Always use uv - Never run Python directly
2. Keep it simple - Avoid unnecessary abstractions
3. Test first - Run test_setup.py before making changes
4. Document clearly - Code should be self-explanatory
5. Handle errors gracefully - Fail fast with clear messages
6. One change at a time - Small, focused commits
7. Monitor verbose output - Use ./monitor.sh during development