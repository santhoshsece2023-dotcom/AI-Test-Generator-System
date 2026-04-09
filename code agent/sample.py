class Calculator:
    def add(self, a, b):
        return a + b
        
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

def process_data(data: list):
    if not data:
        return None
        
    result = 0
    for item in data:
        if isinstance(item, int):
            result += item
        elif isinstance(item, str) and item.isdigit():
            result += int(item)
    return result
