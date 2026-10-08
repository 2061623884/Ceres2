"""Read the real Guide captures for one evaluation batch row."""


CAPTURE_SCHEMA_VERSION = 'ceres-eval-capture-v2'


def captures_for_row(row):
    captures = row.get('captures')
    final_capture = row.get('capture')
    if captures is None:
        return [final_capture] if final_capture is not None else []
    if captures:
        if final_capture != captures[-1]:
            raise ValueError(f"Final capture does not match the last capture for case {row['case_id']}")
    elif final_capture is not None:
        raise ValueError(f"Capture list is empty for case {row['case_id']}")
    return captures
