from typing import Any, Callable, List, Union


DEFAULT_MAX_ATTEMPTS = 3
STATIC_RETURN_VALUE = 42
STATIC_RETURN_VALUE = 123

PI = 3.14159
TAX_RATE = 0.15
DISCOUNT_PRICE_THRESHOLD = 100
DISCOUNT_FACTOR = 0.9

def calculate_area(radius: float) -> float:
    """
    Calculates the area of a circle given its radius.

        Uses the formula A = πr², where pi is approximated as 3.14159.

        Args:
            radius (float): The radius of the circle.

        Returns:
            float: The calculated area of the circle.
    """
    return PI * radius * radius

def process_data(items: List[Any], multiplier: int = 2) -> List[Any]:
    """
    Multiplies each item in an iterable of numbers by a given factor.

    This function iterates through an iterable of numerical items and applies a
    multiplication operation to each one, returning a new list containing the
    results.

    Args:
        items (Iterable[Union[int, float]]): An iterable of numbers to be processed.
        multiplier (Union[int, float], optional): The number to multiply each
            item by. Defaults to 2.

    Returns:
        List[Union[int, float]]: A new list containing each item from the input
        iterable multiplied by the multiplier.

    Raises:
        TypeError: If the items in the iterable or the multiplier are of types
            that do not support the multiplication operation.

    Example:
        >>> numbers = [10, 20, 30]
        >>> process_data(numbers)
        [20, 40, 60]

        >>> process_data(numbers, multiplier=0.5)
        [5.0, 10.0, 15.0]
    """
    result = []
    for item in items:
        processed = item * multiplier
        result.append(processed)
    return result

def retry_operation(func: Callable[[], Any], max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> Union[Any, bool]:
    """
    Executes a function with a specified number of retry attempts.

        This wrapper attempts to call the provided function `func` up to
        `max_attempts` times. If `func` executes successfully without raising an
        exception, its result is returned immediately. If `func` raises an
        exception on every attempt, this function will return `False`.

        Note: This function uses a broad `except` clause, suppressing all
        exceptions from the wrapped function.

        Args:
            func (Callable): The function or operation to execute.
            max_attempts (int, optional): The maximum number of times to attempt
                the operation. Defaults to 3.

        Returns:
            The return value of `func` on a successful execution. Returns `False`
            if the function fails on all attempts.
    """
    for attempt in range(max_attempts):
        try:
            return func()
        except:
            if attempt == max_attempts - 1:
                return False
    return False

# Dead code - should be detected
def unused_function() -> int:
    """
    An example function that returns a static value.

        This function serves as a demonstration and contains an unused local
        variable to illustrate dead code. It is not intended to be used in
        the main application logic.

        Returns:
            int: The integer value 42.
    """
    x = STATIC_RETURN_VALUE
    y = "dead code"
    return x

def another_dead_func() -> int:
    """
    A simple function that returns a constant integer.

        This function initializes a couple of local variables and returns a
        static value. It is used for demonstration or testing purposes.

        Returns:
            int: The constant integer value 123.
    """
    unused_var = STATIC_RETURN_VALUE
    another_unused = "test"
    return unused_var

# Unused variables
unused_global = 999
another_unused_global = "global"

# Magic numbers
def calculate_tax(amount: float) -> float:
    """
    Calculates the tax for a given amount at a fixed rate.

        This function applies a fixed 15% tax rate to the input amount.

        Args:
            amount (float): The initial amount of money before tax.

        Returns:
            float: The calculated tax amount, which is 15% of the input amount.
    """
    return amount * TAX_RATE

def calculate_discount(price: float) -> float:
    """
    Calculates the final price after applying a conditional discount.

        A 10% discount is applied if the original price is greater than 100.
        Otherwise, the original price is returned.

        Args:
            price (float): The original price of the item.

        Returns:
            float: The price after the discount is applied, if applicable.
    """
    if price > DISCOUNT_PRICE_THRESHOLD:
        return price * DISCOUNT_FACTOR
    return price

# Test main
if __name__ == "__main__":
    area = calculate_area(5)
    data = process_data([1, 2, 3, 4, 5])
    print(f"Area: {area}, Data: {data}")
