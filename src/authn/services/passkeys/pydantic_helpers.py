def _pydantic_load(model_cls, data):
    """
    Load a pydantic model from a dict across v1/v2:
    - v2: model_validate
    - v1: parse_obj
    - fallback: constructor
    """
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(data)
    if hasattr(model_cls, "parse_obj"):
        return model_cls.parse_obj(data)
    try:
        return model_cls(**data)
    except Exception:
        return data
