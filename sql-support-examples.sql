-- SQL Support Examples
-- Practical read-only SQL examples for technical support investigations.
-- These examples use fictional tables and data.

-- 1. Find failed transactions
SELECT *
FROM transactions
WHERE status = 'failed';

-- 2. Find transactions for a specific customer
SELECT *
FROM transactions
WHERE customer_id = 12345;

-- 3. Find recent failed transactions
SELECT *
FROM transactions
WHERE status = 'failed'
  AND created_at >= '2026-09-01'
ORDER BY created_at DESC;

-- 4. Count failed transactions
SELECT COUNT(*) AS failed_transaction_count
FROM transactions
WHERE status = 'failed';

-- 5. Count transactions by status
SELECT status, COUNT(*) AS transaction_count
FROM transactions
GROUP BY status
ORDER BY transaction_count DESC;

-- 6. Find a specific transaction
SELECT *
FROM transactions
WHERE transaction_id = 'TXN-10001';

-- 7. Investigate records for one organization
SELECT *
FROM transactions
WHERE organization_id = 5001
ORDER BY created_at DESC;

-- 8. Example JOIN
SELECT t.transaction_id, t.status, c.customer_name
FROM transactions AS t
JOIN customers AS c
  ON t.customer_id = c.customer_id
WHERE t.status = 'failed';

-- Support principle:
-- Use SQL to collect evidence and understand data.
-- Avoid changing production data unless you are authorized
-- and the change is controlled.
