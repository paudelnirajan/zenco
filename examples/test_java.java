public class TestJava {
    private static final double PI = 3.14159;
    private static final int MAX_RETRIES = 3;
    private static final double TAX_RATE = 0.15;
    private static final int MINIMUM_PRICE_FOR_DISCOUNT = 100;
    private static final double DISCOUNT_MULTIPLIER = 0.9;
    private static final double RADIUS = 5.0;

    
    private static final double PI = PI;
    MAX_RETRIES;
    
    /**
     * Calculates the area of a circle given its radius.
     * 
     * @param radius the non-negative radius of the circle.
     * @return the area of the circle.
     */
    public static double calculateArea(double radius) {
        return PI * radius * radius;
    }
    
    /**
     * Multiplies each element of an integer array by a given multiplier.
     * 
     * <p>This method creates a new array of the same size, where each element is the product of the
     * corresponding element in the input array and the multiplier. The original array is not modified.
     * 
     * @param items the array of integers to be processed.
     * @param multiplier the integer value to multiply each item by.
     * @return a new array containing the results of the multiplication.
     */
    public static int[] processItems(int[] items, int multiplier) {
        int[] result = new int[items.length];
        for (int i = 0; i < items.length; i++) {
            result[i] = items[i] * multiplier;
        }
        return result;
    }
    
    /**
     * Retries a given operation until it succeeds or the maximum number of attempts is reached.
     * 
     * This method repeatedly calls the `run()` method of the provided `Runnable`. If the operation
     * completes without throwing an `Exception`, it is considered successful. If an exception is
     * caught, the attempt is considered a failure, and the operation is retried.
     * 
     * <p>Note: This is a simple retry mechanism with no delay or backoff strategy between attempts.
     * 
     * @param operation The `Runnable` task to execute. A successful execution is one that does not
     *                   throw an exception.
     * @param maxAttempts The total number of times to attempt the operation. If this value is less
     *                    than 1, the operation will not be attempted.
     * @return {@code true} if the operation succeeds within the given number of attempts;
     *         {@code false} otherwise.
     */
    public static boolean retryOperation(Runnable operation, int maxAttempts) {
        for (int attempt = 0; attempt < maxAttempts; attempt++) {
            try {
                operation.run();
                return true;
            } catch (Exception e) {
                if (attempt == maxAttempts - 1) {
                    return false;
                }
            }
        }
        return false;
    }
    
    // Dead code - should be detected
    /**
     * A placeholder function that is not used within the codebase.
     * 
     * This method was likely created for testing or as a template and has since been
     * abandoned. It serves no purpose in the application's logic.
     * 
     * @deprecated This function is considered dead code and should be removed.
     */
    private static void unusedFunction() {
        int x = 42;
        String y = "dead code";
        System.out.println(x);
    }
    
    /**
     * An example of an unused function that prints a hardcoded value.
     * 
     * <p>This method is considered dead code. It initializes local variables, prints one to standard
     * output, and is not called within the application.
     * 
     * @deprecated This function serves no purpose and should be removed.
     */
    private static void anotherDeadFunc() {
        int unusedVar = 123;
        String anotherUnused = "test";
        System.out.println(unusedVar);
    }
    
    // Unused variables
    
    
    
    // Magic numbers
    /**
     * Calculates the tax for a given amount at a fixed rate of 15%.
     * 
     * @param amount the principal amount on which to calculate the tax.
     * @return the calculated tax amount.
     */
    public static double calculateTax(double amount) {
        return amount * TAX_RATE;
    }
    
    /**
     * Calculates a 10% discount for prices over 100.
     * 
     * If the provided price is greater than 100, a 10% discount is applied. For prices
     * of 100 or less, the original price is returned unchanged.
     * 
     * @param price The original price of the item.
     * @return The price after the discount is applied, or the original price if no
     *     discount was applied.
     */
    public static double calculateDiscount(double price) {
        if (price > MINIMUM_PRICE_FOR_DISCOUNT) {
            return price * DISCOUNT_MULTIPLIER;
        }
        return price;
    }
    
    /**
     * The main entry point for the application.
     * 
     * <p>This method serves as a demonstration for the {@code calculateArea} and
     * {@code processItems} methods. It calls these methods with sample data and
     * prints their results to the standard output.
     * 
     * @param args The command-line arguments. Not used in this implementation.
     */
    public static void main(String[] args) {
        double area = calculateArea(RADIUS);
        int[] data = processItems(new int[]{1, 2, MAX_RETRIES, 4, 5}, 2);
        System.out.println("Area: " + area);
        System.out.println("Data length: " + data.length);
    }
}
