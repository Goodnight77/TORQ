"""Work-order content builder.

Turns a diagnosis result into a complete work order: repair steps, required
parts, tools, and safety warnings.
"""

# TODO: map DiagnosisResult -> ordered repair steps
# TODO: resolve required parts and tools from manuals/inventory
# TODO: attach safety warnings and estimated time
# TODO: return a WorkOrder schema ready for PDF rendering
