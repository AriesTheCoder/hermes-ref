"""Stable model-facing workspace schema."""

WORKSPACE_SCHEMA = {
    'name': 'ref_workspace',
    'description': (
        'Coordinate substantial shared work in Ref Plans. Bind a known document directly, '
        'or discover once before creating a private outline. Read on follow-ups and update '
        'the same document with verified progress. No final-answer recording. '
        'Load hermes-ref:workspace for the workflow. Report failures once, without retry loops.'
    ),
    'parameters': {
        'type': 'object',
        'properties': {
            'action': {'type': 'string', 'enum': ['discover', 'begin', 'bind', 'read', 'update', 'status']},
            'title': {'type': 'string', 'minLength': 1, 'maxLength': 200},
            'content': {
                'type': 'string', 'maxLength': 60000,
                'description': 'Outline beginning with matching h1, then Scope, Decisions, Tasks and Verification. Never copied chat output.',
            },
            'plan_id': {'type': 'string', 'pattern': '^[A-Za-z0-9_-]{8,80}$'},
            'offset': {'type': 'integer', 'minimum': 0, 'maximum': 50000},
            'old_string': {
                'type': 'string', 'minLength': 1, 'maxLength': 60000,
                'description': 'Required for update: a non-empty passage matching exactly once.',
            },
            'new_string': {
                'type': 'string', 'maxLength': 60000,
                'description': 'Required for update and must differ from old_string. Supply an explicit empty string for intentional deletion; omission is an error.',
            },
        },
        'required': ['action'],
        'additionalProperties': False,
    },
}
