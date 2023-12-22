SELECT
    elem::json->>'orderItemId' as order_item_id,
    elem::json->>'orderId' as order_id,
    elem::json->>'fsn' as fsn,
    elem::json->>'hsn' as hsn,
    elem::json->>'sku' as sku,
    elem::json->>'title' as title,
    elem::json->>'status' as status,
    (elem::json->>'quantity')::integer as quantity,
    elem::json->>'listingId' as listing_id,
    elem::json->>'orderDate' as order_date,
    elem::json->>'packageIds' as package_ids,
    elem::json->>'paymentType' as paymentType,
    (elem::json->>'is_replacement')::boolean as is_replacement,
    elem::json->>'serviceProfile' as service_profile,
    elem::json->>'priceComponents' as price_components,
    elem::json->>'cancellationGroupId' as cancellation_group_id,
    shipments."shipmentId" as shipment_id,
    shipments.shipment_status_state
FROM {{ source('tap_flipkart', 'shipments') }},
    unnest("orderItems"::jsonb[]) as elem