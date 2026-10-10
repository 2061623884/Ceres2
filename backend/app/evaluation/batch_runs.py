"""Read the real Guide captures for one evaluation batch row."""

from app.evaluation.annotate_runs import RunAnnotation


CAPTURE_SCHEMA_VERSION = 'ceres-eval-capture-v2'
ANNOTATION_SCHEMA_VERSION = 'ceres-run-annotation-v2'


def annotation_for_capture(capture, context):
    if capture['schema_version'] != CAPTURE_SCHEMA_VERSION:
        raise ValueError(f'Unsupported capture schema_version for {context}')
    labels = capture['labels']
    if labels is None:
        return None
    if labels['schema_version'] != ANNOTATION_SCHEMA_VERSION:
        raise ValueError(f'Unsupported annotation schema_version for {context}')
    annotation = RunAnnotation.model_validate({
        field: value for field, value in labels.items()
        if field != 'schema_version'
    })
    if (annotation.owner_id, annotation.run_id) != (capture['owner_id'], capture['run_id']):
        raise ValueError(f'Annotation owner/run mismatch for {context}')
    return annotation


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
