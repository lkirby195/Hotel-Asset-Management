def report_cache_key(
    tenant_id: str,
    report_type: str,
    property_id: str,
    period: str,
    start: str,
    end: str,
) -> str:
    return f"hotel_am:{tenant_id}:report:{report_type}:{property_id}:{period}:{start}:{end}"


def report_children_cache_key(
    tenant_id: str,
    property_id: str,
    parent_id: str,
    period: str,
) -> str:
    return f"hotel_am:{tenant_id}:children:{property_id}:{parent_id}:{period}"


def tenant_invalidation_pattern(tenant_id: str, property_id: str | None = None) -> str:
    if property_id:
        return f"hotel_am:{tenant_id}:*:{property_id}:*"
    return f"hotel_am:{tenant_id}:*"
