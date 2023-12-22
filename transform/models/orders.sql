SELECT
    order_id,
    order_date,
    COUNT(DISTINCT order_item_id) as order_items_count
FROM {{ ref('order_items') }}
GROUP BY 1, 2
