# Known Issues & Bug Tracker

## Active Issues

### ✅ FIXED: Streamlit cache pickle error with datetime
**Status:** FIXED
**Reported:** 2026-01-09
**Pages affected:** All pages (Race Confidence primarily)
**Error:**
```
NotImplementedError: (dtype('<M8[ns]'), array([...]))
Error from: pickle.loads(pickled_entry)
```

**Root cause:** Streamlit's @st.cache_data tries to pickle pandas DataFrames with datetime columns, which fails in pandas 2.3+

**Fix:**
1. Cleared cache: Run `CLEAR-CACHE.bat` or delete `.streamlit` folder
2. Updated all pages to use `@st.cache_data(ttl=300)` instead of `@st.cache_data`
   - ttl=300 means cache expires after 5 minutes
   - Avoids complex pickling of datetime objects

**How to fix if it happens again:**
- Double-click: `CLEAR-CACHE.bat`
- Or manually delete: `.streamlit` folder in project root
- Restart dashboard

---

### ✅ FIXED: PyArrow module not found error
**Status:** FIXED (Final solution)
**Reported:** 2026-01-09
**Pages affected:** All pages with tables
**Error:**
```
ModuleNotFoundError: No module named 'pyarrow'
Error at: st.dataframe(), st.table() - both require pyarrow in Streamlit 1.52+
```

**Root cause:** PyArrow cannot be built/installed on ARM64 Windows. Streamlit 1.52+ requires pyarrow for ALL table display methods (st.dataframe and st.table).

**Fix:** Replaced ALL table displays with markdown tables:
- `dashboard/pages/1_📊_Consistency.py` - 2 tables converted to markdown
- `dashboard/pages/2_🎯_Season_Compare.py` - 1 table converted to markdown
- `dashboard/pages/3_🏁_Race_Confidence.py` - 1 table converted to markdown

**How it works now:**
- Generate markdown tables manually: `st.markdown("| Col1 | Col2 |")`
- Loop through dataframe rows to create table rows
- NO pyarrow dependency at all

**Impact:** All tables now display correctly without pyarrow! Works on ARM64 Windows.

---

### ℹ️ PyArrow warning (cosmetic only)
**Status:** INFORMATIONAL
**Impact:** None - warning only, all features work
**Message:**
```
pyarrow>=7.0 required but not installed
```

**Why:** PyArrow can't build on ARM64 Windows. Not needed after our fixes above.

**Action:** Ignore the warning - it's harmless

---

## Resolved Issues

### ✅ Dashboard date formatting error
**Status:** FIXED
**Reported:** 2026-01-09
**Fixed:** 2026-01-09
**Pages affected:** Consistency Guardian
**Error:**
```
Error loading data: (dtype('<M8[ns]'), array([...]))
```

**Root cause:** Pandas `.astype(str)` on datetime column returns tuple instead of strings in newer pandas 2.3+ versions.

**Fix:** Changed line 95 in `dashboard/utils/data_loader.py`:
```python
# Before:
'date_only': lambda x: ', '.join(sorted(set(x.astype(str))))

# After:
'date_only': lambda x: ', '.join(sorted([str(d) for d in set(x)]))
```

**Resolution:** Use list comprehension with `str()` instead of `.astype(str)` for better compatibility.

---

## How to Report Issues

If you encounter problems:

1. **Note the error message** (screenshot or copy text)
2. **Note which page** (Consistency / Season Compare / Race Confidence)
3. **Note what you were doing** (clicking button, selecting filter, etc.)
4. **Add to this file** under "Active Issues"

## Format for New Issues

```markdown
### ❌ [Short description]
**Status:** OPEN
**Reported:** [Date]
**Pages affected:** [Page name]
**Error:**
[Error message or description]

**Steps to reproduce:**
1. Step 1
2. Step 2
3. Error occurs

**Workaround:** [If any]
```

---

## Future Enhancements (Not Bugs)

### 📋 Wishlist

- [ ] Export charts as images
- [ ] Calendar heatmap view
- [ ] Email alerts for floor violations
- [ ] Pace zone distribution analysis
- [ ] Form metrics from FIT files
- [ ] Custom season date ranges
- [ ] Multi-year trend charts

Add your ideas here!
