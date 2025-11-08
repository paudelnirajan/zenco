import collections

class CodeTransformer:
    """
    A class to manage and apply changes to a source code file.
    Changes are collected and then applied in reverse order to avoid byte offset issues.
    """
    def __init__(self, source_bytes: bytes):
        self.source_bytes = source_bytes
        self.changes = []

    def add_change(self, start_byte: int, end_byte: int, new_text: str):
        """Adds a change to the list of pending transformations."""
        self.changes.append({
            "start_byte": start_byte,
            "end_byte": end_byte,
            "new_text": new_text.encode('utf8')
        })

    def apply_changes(self) -> bytes:
        """
        Applies all collected changes to the source code.
        Sorts changes by start_byte in reverse order before applying to
        ensure that subsequent changes do not affect the byte offsets of
        earlier ones.
        """
        if not self.changes:
            return self.source_bytes

        self.changes.sort(key=lambda c: c['start_byte'], reverse=True)

        source_parts = []
        last_byte = len(self.source_bytes)

        for change in self.changes:
            source_parts.append(self.source_bytes[change['end_byte']:last_byte])
            source_parts.append(change['new_text'])
            last_byte = change['start_byte']

        source_parts.append(self.source_bytes[:last_byte])

        return b"".join(reversed(source_parts))