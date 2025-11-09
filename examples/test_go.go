package main

import "fmt"

const PI = 3.14159
const MAX_RETRIES = 3

/**
 * calculateArea calculates the area of a circle given its radius.
 * 
 * Args:
 *     radius: The radius of the circle.
 * 
 * Returns:
 *     The area of the circle as a float64.
 */
func calculateArea(radius float64) float64 {
	return PI * radius * radius
}

/**
 * processItems multiplies each integer in the `items` slice by the `multiplier`.
 * 
 * It returns a new slice containing the results and does not modify the
 * original input slice.
 */
func processItems(items []int, multiplier int) []int {
	result := make([]int, len(items))
	for i, item := range items {
		result[i] = item * multiplier
	}
	return result
}

/**
 * retryOperation attempts to execute a given operation, retrying on failure.
 * 
 * It repeatedly calls the provided `operation` function until it returns `true` or
 * the `maxAttempts` limit is reached. The `operation` function is expected to
 * return `true` for success and `false` for failure.
 * 
 * Args:
 *     operation: The function to execute. Must return a boolean indicating success.
 *     maxAttempts: The maximum number of times to attempt the operation.
 * 
 * Returns:
 *     A boolean value: true if the operation succeeded within the allowed
 *     attempts, and false otherwise.
 */
func retryOperation(operation func() bool, maxAttempts int) bool {
	for attempt := 0; attempt < maxAttempts; attempt++ {
		if operation() {
			return true
		}
	}
	return false
}

// Dead code - should be detected
/**
 * unusedFunction is a sample function intended to demonstrate unused code.
 * It performs a trivial action and always returns the constant value 42.
 * 
 * Deprecated: This function is for demonstration purposes only and should not be used.
 */
func unusedFunction() int {
	x := 42
	y := "dead code"
	fmt.Println(y)
	return x
}

/**
 * anotherDeadFunc is a deprecated example function that returns a fixed integer.
 * It also prints a string to standard output as a side effect.
 * 
 * Deprecated: This function is for demonstration purposes only and should not
 * be used. There is no replacement.
 */
func anotherDeadFunc() int {
	unusedVar := 123
	anotherUnused := "test"
	fmt.Println(anotherUnused)
	return unusedVar
}

// Unused variables
var unusedGlobal = 999
var anotherUnusedGlobal = "global"

// Magic numbers
/**
 * Calculates a 15% tax for the provided amount.
 * 
 * Args:
 *     amount (float64): The principal amount on which to calculate the tax.
 * 
 * Returns:
 *     float64: The calculated tax amount.
 */
func calculateTax(amount float64) float64 {
	return amount * 0.15
}

/**
 * calculateDiscount applies a 10% discount to prices over 100.
 * 
 * If the input price is greater than 100, this function returns the price reduced
 * by 10%. Otherwise, it returns the original, unmodified price.
 */
func calculateDiscount(price float64) float64 {
	if price > 100 {
		return price * 0.9
	}
	return price
}

/**
 * main is the entry point for the application. It demonstrates the usage of the
 * calculateArea and processItems functions by executing them with sample data
 * and printing the results to standard output.
 */
func main() {
	area := calculateArea(5.0)
	data := processItems([]int{1, 2, 3, 4, 5}, 2)
	fmt.Printf("Area: %.2f, Data length: %d\n", area, len(data))
}
