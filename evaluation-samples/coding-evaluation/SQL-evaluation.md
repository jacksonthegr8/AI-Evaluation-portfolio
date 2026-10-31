# Coding Evaluation Sample: SQL Aggregation with Edge-Case Handling

Evaluator: Kanu Jackson Chimeremeze 
Date: July 2026  
Domain: SQL / Database Query Evaluation  
Rubric Dimensions: Correctness, Efficiency, Edge-Case Handling, Instruction Adherence


## A. Prompt & Context

User Query:  
"Write a SQL query to find the average order value for each customer who has placed more than 2 orders. Include customers who have no orders yet, showing their average as 0. Return columns: `customer_name`, `avg_order_value`."

Schema:
'''sql
customers (customer_id INT PK, customer_name VARCHAR)
orders (order_id INT PK, customer_id INT FK, amount DECIMAL)'''

Ambiguity Note: This prompt admits two valid readings:

Reading A: Show only customers with >2 orders, plus zero-order customers (showing 0).

Reading B: Show all customers; display actual average only if >2 orders, otherwise 0.

The original AI response follows Reading A. The evaluation grades under both readings where they diverge.

## B. Original AI Response (Before)

SELECT 
    c.customer_name,
    AVG(o.amount) AS avg_order_value
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name
HAVING COUNT(o.order_id) > 2;

## C. Error Analysis

| # | Finding | Dimension | Severity (Reading A) | Severity (Reading B) | Issue |

| 1 | Incorrect Join Type | Correctness | High | High | Uses `INNER JOIN`, excluding customers with zero orders. Required: "Include customers who have no orders yet." |
| 2 | HAVING Filters Zero-Order Customers | Instruction Adherence | N/A | High | Under Reading B, zero-order customers are filtered out by `HAVING COUNT(o.order_id) > 2` (their count is 0, not >2). |
| 3 | Unhandled NULL Arithmetic | Edge-Case Handling | N/A | Medium | Under Reading B, `LEFT JOIN` would produce NULL averages for zero-order customers; prompt requires displaying 0. The original query never produces NULL because the inner join excludes those rows entirely, so this finding does not apply to the original code. |
| 4 | Silent Ambiguity Resolution | Completeness | Low | Low | The AI chose Reading A without acknowledging the alternative interpretation. A robust response should explicitly state the assumption or handle both cases. |


## D. Live Test: SQLite Demonstration

Test Data:
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    customer_name TEXT
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    amount DECIMAL
);

INSERT INTO customers VALUES 
    (1, 'Alice'),    -- 3 orders, qualifies
    (2, 'Bob'),      -- 2 orders, does not qualify
    (3, 'Carol'),    -- 0 orders, zero-order case
    (4, 'David');    -- 1 order, does not qualify

INSERT INTO orders VALUES 
    (101, 1, 100.00),
    (102, 1, 200.00),
    (103, 1, 300.00),  -- Alice: 3 orders, avg = 200
    (201, 2, 50.00),
    (202, 2, 150.00);  -- Bob: 2 orders, excluded by HAVING


Original Query Output:

customer_name	avg_order_value
Alice	             200.0

Result: Only Alice appears. Bob, carol,and David are exculded. Carol by the inner join, Bob and David by the HAVING clause.

## E. Rewritten Response + Justification 

Reading A Implementation (show qualifying customers + zero-order customers):
SELECT c.customer_name, COALESCE(s.avg_amount, 0) AS avg_order_value
FROM customers c
LEFT JOIN (
    SELECT customer_id, COUNT(*) AS order_count, AVG(amount) AS avg_amount
    FROM orders GROUP BY customer_id
) s ON c.customer_id = s.customer_id
WHERE s.order_count IS NULL OR s.order_count > 2;

Reading B Implementation(show all customers, 0 if ≤2 orders):
SELECT 
    c.customer_name,
    CASE 
        WHEN order_stats.order_count > 2 THEN order_stats.avg_amount
        ELSE 0
    END AS avg_order_value
FROM customers c
LEFT JOIN (
    SELECT 
        customer_id,
        COUNT(*) AS order_count,
        AVG(amount) AS avg_amount
    FROM orders
    GROUP BY customer_id
) order_stats ON c.customer_id = order_stats.customer_id;

Justification:
  Aspect	                                                           Handling
Completeness	               LEFT JOIN ensures all customers appear, including zero-order cases.
Threshold Logic	               Subquery pre-aggregates; outer query applies business logic cleanly. 
                               Reading A filters   in the subquery; Reading B filters in the outer query.
NULL Safety	                   COALESCE (Reading A) or CASE with explicit ELSE 0 (Reading B) ensures 
                               zero-order customers display 0, not NULL.
Correctness	                   Both readings satisfy their respective interpretations of the prompt.

Performance Note: The subquery approach computes aggregates once per customer. For the one-to-many customers→orders relationship, this avoids redundant grouping on a potentially inflated join result. However, modern query optimizers often handle both approaches similarly; the subquery pattern is preferred for clarity and maintainability, not dramatic performance gains.
