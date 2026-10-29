# Coding Evaluation Sample: SQL Aggregation with Edge-Case Handling

Evaluator: Kanu Jackson Chimeremeze 
Date: July 2024  
Domain: SQL / Database Query Evaluation  
Rubric Dimensions: Correctness, Efficiency, Edge-Case Handling, Instruction Adherence


## A. Prompt & Context

User Query:  
"Write a SQL query to find the average order value for each customer who has placed more than 2 orders. Include customers who have no orders yet, showing their average as 0. Return columns: `customer_name`, `avg_order_value`."

Schema:
```sql
customers (customer_id INT PK, customer_name VARCHAR)
orders (order_id INT PK, customer_id INT FK, amount DECIMAL)

## B. Original AI Response(Before)

SELECT 
    c.customer_name,
    AVG(o.amount) AS avg_order_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name
HAVING COUNT(o.order_id) > 2;

## C. Error Analysis

Finding 1: Incorrect Join Type — Missing Customers with Zero Orders
Dimension: Correctness
Severity: High
Issue: The query uses an INNER JOIN, which excludes customers who have placed no orders. The prompt explicitly requires: "Include customers who have no orders yet, showing their average as 0." This makes the result set incomplete.

Finding 2: HAVING Clause Filters Out Valid Zero-Order Customers
Dimension: Instruction Adherence
Severity: High
Issue: The HAVING COUNT(0.order_id) > 2 condition is applied after grouping. Even if the join were corrected to LEFT JOIN, customers with 0 orders would be filtered out because their count is 0, not greater than 2. The prompt asks to show all customers but calculate averages only for those with >2 orders — or alternatively, the phrasing implies showing 0 for customers below the threshold. The AI's interpretation excludes them entirely.

Finding 3: Unhandled NULL Arithmetic
Dimension: Edge-Case Handling
Severity: Medium
Issue: For customers with no orders, AVG(o.amount) would return NULL rather than 0. The prompt specifies the display value should be 0. The AI did not use COALESCE() to handle this.

Finding 4: Ambiguous Threshold Interpretation
Dimension: Completeness
Severity: Low
Issue: The prompt can be read two ways: (a) show only customers with >2 orders, or (b) show all customers but display 0 for those with ≤2. The AI chose (a) without acknowledging the ambiguity. A robust response should either handle both or explicitly state the assumption.

## D. Rewritten Response + Justification

SELECT 
    c.customer_name,
    COALESCE(
        CASE 
            WHEN order_counts.order_count > 2 
            THEN order_counts.avg_amount 
            ELSE 0 
        END, 
        0
    ) AS avg_order_value
FROM customers c
LEFT JOIN (
    SELECT 
        customer_id,
        COUNT(*) AS order_count,
        AVG(amount) AS avg_amount
    FROM orders
    GROUP BY customer_id
) order_counts ON c.customer_id = order_counts.customer_id;

Justification:

1. Completeness: Uses LEFT JOIN from customers to ensure every customer appears in the result, including those with zero orders.
2. Threshold Logic: The subquery pre-aggregates order statistics. The outer query checks order_count > 2 and returns the actual average only for qualifying customers; all others get 0.
3. NULL Safety: COALESCE(..., 0) guarantees that customers with no orders display 0 instead of NULL.
4. Efficiency: The subquery approach computes aggregates once per customer rather than inflating the join and aggregating across a Cartesian-like intermediate result. For large datasets, this is more performant than a naive LEFT JOIN followed by GROUP BY on the full Cartesian product.

The original response failed on three critical dimensions: correctness (wrong join), instruction adherence (excluded zero-order customers), and edge-case handling (NULL display). The rewrite satisfies all stated requirements while maintaining query efficiency.