# Execution Priority & Modular Architecture

## 🎯 **Problem Solved**

Previously, zenco processed code in this order:
```
1. Generate docstrings for ALL functions (including dead code) ❌
2. Add type hints for ALL functions (including dead code) ❌
3. Fix magic numbers for ALL functions (including dead code) ❌
4. Detect dead code and remove it ❌
```

**Result:** Wasted LLM API calls on functions that would be deleted!

## ✅ **New Optimized Order**

With the modular processor architecture:
```python
# 1. Detect dead code FIRST
dead_functions = dead_code_processor.process()

# 2. Generate docstrings (skip dead functions)
docstring_processor.process(generator, dead_functions=dead_functions)

# 3. Add type hints (skip dead functions)
type_hint_processor.process(generator, dead_functions=dead_functions)

# 4. Fix magic numbers (skip dead functions)
magic_number_processor.process(generator, dead_functions=dead_functions)
```

**Result:** 
- ✅ Save LLM API costs
- ✅ Faster processing
- ✅ Cleaner output
- ✅ Better user experience

## 📦 **Module Structure**

```
autodoc_ai/
└── processors/
    ├── __init__.py                  # Exports all processors
    ├── base.py                      # BaseProcessor abstract class
    ├── dead_code_processor.py       # Dead code detection
    ├── docstring_processor.py       # Docstring generation
    ├── type_hint_processor.py       # Type hint addition
    └── magic_number_processor.py    # Magic number replacement
```

## 🔧 **Integration Example**

```python
from autodoc_ai.processors import (
    DeadCodeProcessor,
    DocstringProcessor,
    TypeHintProcessor,
    MagicNumberProcessor
)

# Initialize processors
dead_code_proc = DeadCodeProcessor(lang, tree, source_bytes, transformer)
docstring_proc = DocstringProcessor(lang, tree, source_bytes, transformer)
type_hint_proc = TypeHintProcessor(lang, tree, source_bytes, transformer)
magic_num_proc = MagicNumberProcessor(lang, tree, source_bytes, transformer)

# Execute in priority order
if dead_code:
    dead_functions = dead_code_proc.process(in_place=in_place, strict=strict)
else:
    dead_functions = set()

if docstrings_enabled:
    docstring_proc.process(generator, overwrite_existing, dead_functions)

if add_type_hints:
    type_hint_proc.process(generator, dead_functions)

if fix_magic_numbers:
    magic_num_proc.process(generator, dead_functions)
```

## 📊 **Benefits**

| Metric | Before | After |
|--------|--------|-------|
| **LLM API Calls** | All functions | Only live functions |
| **Processing Time** | Slower | Faster |
| **Code Organization** | 1991 lines in cli.py | Modular processors |
| **Maintainability** | Difficult | Easy |
| **Testing** | Hard to test | Easy to unit test |

## 🚀 **Next Steps**

To fully integrate this architecture:

1. **Update cli.py**: Replace inline processing logic with processor calls
2. **Migrate existing logic**: Move current implementation into processor classes
3. **Add tests**: Unit test each processor independently
4. **Document**: Add docstrings and usage examples
5. **Benchmark**: Measure performance improvements

## 💡 **Implementation Status**

- ✅ Base architecture created
- ✅ Execution priority concept implemented
- ✅ Dead code processor (Python) - **WORKING**
- ⚠️ Other processors - **STUB implementations** (need migration)
- ⚠️ CLI integration - **TODO** (requires refactoring)

## 📝 **Migration Guide**

To migrate existing cli.py logic:

1. Extract each feature's logic into its processor
2. Ensure each processor accepts `dead_functions` parameter
3. Update cli.py to call processors in order
4. Test each language independently
5. Verify all features still work correctly
