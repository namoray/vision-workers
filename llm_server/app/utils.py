def determine_needs_await(cuda_version: str) -> bool:
    # only needs 'await' statment for cuda118
    # TODO: CHANGE BACK
    return True
    return float(cuda_version) < 12.1
