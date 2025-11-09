const TAX_RATE = 0.15;
const PI = 3.14159;
const MINIMUM_PRICE_FOR_DISCOUNT = 100;
const DISCOUNT_MULTIPLIER = 0.9;
const SAMPLE_RADIUS = 5;

const MAX_ATTEMPTS = 3;

/**
 * Calculates the area of a circle given its radius.
 * 
 * @param {number} radius The radius of the circle.
 * @returns {number} The calculated area of the circle.
 */
function calculateArea(radius) {
    return PI * radius * radius;
}

/**
 * Processes a list of numbers by multiplying each item by a given factor.
 * 
 * This function iterates through an array of numbers, applies a multiplication
 * operation to each element, and returns a new array with the transformed
 * values. The original array is not modified.
 * 
 * @param {Array<number>} items The array of numbers to be processed.
 * @param {number} [multiplier=2] The factor to multiply each item by.
 * @returns {Array<number>} A new array containing the processed numbers.
 */
function processItems(items, multiplier = 2) {
    const result = [];
    for (let i = 0; i < items.length; i++) {
        const processed = items[i] * multiplier;
        result.push(processed);
    }
    return result;
}

/**
 * Attempts to execute an operation, retrying on failure.
 * 
 * This function repeatedly calls the provided operation until it succeeds or
 * the maximum number of attempts is reached. An operation is considered
 * successful if it does not throw an error.
 * 
 * @param {function():*} operation The function to execute.
 * @param {number=} [maxAttempts=MAX_ATTEMPTS] The maximum number of attempts
 *     to make.
 * @returns {*|boolean} The result of the operation if successful, otherwise false
 *     if all attempts fail.
 */
function retryOperation(operation, maxAttempts = MAX_ATTEMPTS) {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
            return operation();
        } catch (error) {
            if (attempt === maxAttempts - 1) {
                return false;
            }
        }
    }
    return false;
}

// Dead code - should be detected
/**
 * An example of an unused or deprecated function.
 * 
 * This function serves as a placeholder or example of dead code. It contains
 * an unused variable and always returns a hardcoded value. It should not be
 * used in production code.
 * 
 * @deprecated This function is an example and has no real-world use case.
 * @returns {number} The constant value 42.
 */
function unusedFunction() {
    const x = 42;
    const y = "dead code";
    return x;
}

/**
 * An example of a deprecated function that returns a static value.
 * 
 * This function is a placeholder and should not be used in production code.
 * It contains unused local variables and its return value is constant.
 * 
 * @deprecated This function is an example and is not intended for use.
 * @returns {number} The constant integer 123.
 */
function anotherDeadFunc() {
    const unusedVar = 123;
    const anotherUnused = "test";
    return unusedVar;
}

// Unused variables

// Magic numbers
/**
 * Calculates the tax for a given amount at a fixed rate of 15%.
 * 
 * @param {number} amount The base amount for which to calculate the tax.
 * @returns {number} The calculated tax amount (15% of the base amount).
 */
function calculateTax(amount) {
    return amount * TAX_RATE;
}

/**
 * Calculates the final price after applying a discount.
 * 
 * Applies a 10% discount to any price greater than 100. Prices of 100 or
 * less are returned unmodified.
 * 
 * Args:
 *     price: The original price of the item.
 * 
 * Returns:
 *     The final price after the discount, or the original price if no
 *     discount was applied.
 */
function calculateDiscount(price) {
    if (price > MINIMUM_PRICE_FOR_DISCOUNT) {
        return price * DISCOUNT_MULTIPLIER;
    }
    return price;
}

// Test execution
console.log(calculateArea(SAMPLE_RADIUS));
console.log(processItems([1, 2, 3, 4, 5]));
