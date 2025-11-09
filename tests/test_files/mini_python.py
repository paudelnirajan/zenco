def calculate_area(radius):
    return 3.14159 * radius * radius

def process_numbers(nums):
    result = []
    for n in nums:
        result.append(n * 2)
    return result

def unused_function():
    x = 42
    return x

unused_var = 999

if __name__ == "__main__":
    area = calculate_area(5)
    print(area)
