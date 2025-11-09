#include <iostream>
#include <vector>
#include <cmath>

constexpr auto PI = 3.14159;
constexpr auto MAX_RETRIES = 3;
constexpr auto TAX_RATE = 0.15;
constexpr auto MINIMUM_PRICE_FOR_DISCOUNT = 100;
constexpr auto DISCOUNT_MULTIPLIER = 0.9;

const double PI = PI;
MAX_RETRIES;

/**
 * Calculates the area of a circle given its radius.
 * 
 * This function computes the area using the formula A = π * r^2. It assumes
 * the existence of a pre-defined `PI` constant.
 * 
 * Args:
 *   radius: The radius of the circle. Should be a non-negative value.
 * 
 * Returns:
 *   The area of the circle as a double.
 */
double calculateArea(double radius) {
    return PI * radius * radius;
}

/**
 * Multiplies each element in a vector of integers by a given multiplier.
 * 
 * This function iterates through the input vector, multiplies each element
 * by the provided multiplier, and stores the result in a new vector. The
 * original input vector is not modified.
 * 
 * Args:
 *   items: A constant reference to a vector of integers to be processed.
 *   multiplier: The integer value to multiply each element in `items` by.
 * 
 * Returns:
 *   A new std::vector<int> where each element is the product of the
 *   corresponding element in the input vector and the multiplier.
 */
std::vector<int> processItems(const std::vector<int>& items, int multiplier) {
    std::vector<int> result;
    for (int item : items) {
        result.push_back(item * multiplier);
    }
    return result;
}

/**
 * Attempts to execute a given operation up to a maximum number of times.
 * 
 * This function provides a simple retry mechanism. It repeatedly calls the provided
 * `operation` function until it returns true or until `maxAttempts` have been
 * made. This is useful for operations that might fail transiently.
 * 
 * Args:
 *   operation: A pointer to a function that performs the desired operation.
 *     The function should take no arguments and return true on success and
 *     false on failure.
 *   maxAttempts: The maximum number of times to try the operation before giving
 *     up.
 * 
 * Returns:
 *   true if the operation succeeds within the given number of attempts,
 *   false otherwise.
 */
bool retryOperation(bool (*operation)(), int maxAttempts) {
    for (int attempt = 0; attempt < maxAttempts; attempt++) {
        if (operation()) {
            return true;
        }
    }
    return false;
}

// Dead code - should be detected
/**
 * An unused demonstration function.
 * 
 * This function is not called from anywhere in the codebase and serves as a
 * placeholder or an example of dead code. It initializes local variables and
 * prints a value to the standard output, but has no other side effects.
 */
void unusedFunction() {
    int x = 42;
    std::string y = "dead code";
    std::cout << x << std::endl;
}

/**
 * A demonstration function that prints a value to standard output.
 * 
 * Initializes two local variables, one integer and one string. The value of the
 * integer is printed to `std::cout`, while the string variable is unused.
 * This function serves as a simple example and has no return value.
 */
void anotherDeadFunc() {
    int unusedVar = 123;
    std::string anotherUnused = "test";
    std::cout << unusedVar << std::endl;
}

// Unused variables



// Magic numbers
/**
 * Calculates the tax for a given amount.
 * 
 * This function applies a fixed tax rate of 15% to the input amount.
 * 
 * Args:
 *   amount: The principal amount on which the tax is calculated.
 * 
 * Returns:
 *   The calculated tax amount.
 */
double calculateTax(double amount) {
    return amount * TAX_RATE;
}

/**
 * Calculates the final price after applying a conditional discount.
 * 
 * A 10% discount is applied if the input price is greater than 100.
 * Otherwise, the original price is returned.
 * 
 * Args:
 *   price: The original price of the item before any discounts.
 * 
 * Returns:
 *   The final price after the discount is applied, if applicable.
 */
double calculateDiscount(double price) {
    if (price > MINIMUM_PRICE_FOR_DISCOUNT) {
        return price * DISCOUNT_MULTIPLIER;
    }
    return price;
}

/**
 * The main entry point for the application.
 * 
 * Demonstrates the use of the `calculateArea` and `processItems` functions.
 * It calculates the area for a predefined value, processes a sample vector of
 * integers, and prints the results to the standard output.
 * 
 * Returns:
 *     0 on successful execution.
 */
int main() {
    double area = calculateArea(5.0);
    std::vector<int> data = processItems({1, 2, MAX_RETRIES, 4, 5}, 2);
    std::cout << "Area: " << area << ", Data length: " << data.size() << std::endl;
    return 0;
}
